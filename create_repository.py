#!/usr/bin/env python

import collections
import errno
import gzip
import hashlib
import io
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
import xml.etree.ElementTree
import zipfile


def main():
    outpu_folder  = "./repo"
    addon_paths = [
        "https://github.com/mao2009/maorepo.git:addons/repository.maorepo",
        "https://github.com/mao2009/kodi-addon-takoyaki.git:script.module.takoyaki"
    ]

    is_compressed = False

    KodiRepository.create(outpu_folder, addon_paths, is_compressed)


class KodiRepository(object):
    __metadata = collections.namedtuple(
        'Metadata', ('id', 'version', 'root'))
    __worker_result = collections.namedtuple(
        'WorkerResult', ('metadata', 'exc_info'))
    __addon_worker = collections.namedtuple(
        'AddonWorker', ('thread', 'result_slot'))

    __INFO_BASENAME = 'addon.xml'
    __METADATA_BASENAMES = (
        __INFO_BASENAME,
        'icon.png',
        'fanart.jpg',
        'LICENSE.txt')

    @classmethod
    def get_archive_basename(cls, metadata):
        return '{}-{}.zip'.format(metadata.id, metadata.version)

    @classmethod
    def get_metadata_basenames(cls, metadata):
        return ([(name, name) for name in cls.__METADATA_BASENAMES] +
            [(
                'changelog.txt',
                'changelog-{}.txt'.format(metadata.version))])

    @classmethod
    def is_url(cls, path):
        return bool(re.match('[A-Za-z0-9+.-]+://.', path))
    
    @classmethod
    def get_posix_path(cls, path):
        return path.replace(os.path.sep, '/')

    @classmethod
    def validate_id(cls, id):
        if id is None or re.match('[^a-z0-9._-]', id):
            return False
        else:
            return True

    @classmethod
    def validate_version(cls, version):
         return (version is not None
            and re.match(
                    r'(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){2}(?:[-~][0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z',
                    version))

    @classmethod
    def parse_metadata(cls, metadata_file):
        try:
            tree = xml.etree.ElementTree.parse(metadata_file)
        except IOError:
            raise RuntimeError('Cannot open addon metadata: {}'.format(metadata_file))

        root = tree.getroot()

        metadata = cls.__metadata(
            root.get('id'),
            root.get('version'),
            root)

        if not cls.validate_id(metadata.id):
            raise RuntimeError('Invalid addon ID: {}'.format(metadata.id))

        if not cls.validate_version(metadata.version):
            raise RuntimeError('Invalid addon verson: {}'.format(metadata.version))

        return metadata

    @classmethod
    def generate_checksum(cls, archive_path, is_binary=True, checksum_path=None):
        checksum_path = '{}.md5'.format(archive_path) if checksum_path is None else checksum_path
        checksum_dirname = os.path.dirname(checksum_path)
        archive_relpath = os.path.relpath(archive_path, checksum_dirname)

        checksum = hashlib.md5()
        with open(archive_path, 'rb') as archive_contents:
            for chunk in iter(lambda: archive_contents.read(2**12), b''):
                checksum.update(chunk)
        digest = checksum.hexdigest()

        binary_marker = '*' if is_binary else ' '

        with io.open(checksum_path, 'w', newline='\n') as sig:
            sig.write(u'{} {}{}\n'.format(digest, binary_marker, archive_relpath))

    @classmethod
    def copy_metadata_files(cls, source_folder, target_folder, metadata):
        for (source_basename, target_basename) in cls.get_metadata_basenames(metadata):
            source_path = os.path.join(source_folder, source_basename)
            if os.path.isfile(source_path):
                shutil.copyfile(source_path, os.path.join(target_folder, target_basename))

    @classmethod
    def create_git_archive(cls, target_folder, metedata, clone_path, cloned):
        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)
                
        archive_path = os.path.join(target_folder, cls.get_archive_basename(metedata))

        with open(archive_path, 'wb') as archive:
            cloned.archive(
                archive,
                treeish='HEAD:{}'.format(clone_path),
                prefix=cls.get_posix_path(os.path.join(metedata.id, '')),
                format='zip')
        
        return archive_path

    @classmethod
    def create_folder_archive(cls, target_folder, metedata, addon_path):
        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)
        archive_path = os.path.join(
            target_folder, cls.get_archive_basename(metedata))
        with zipfile.ZipFile(
                archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for (root, dirs, files) in os.walk(addon_path):
                relative_root = os.path.join(
                    metedata.id,
                    os.path.relpath(root, addon_path))
                for relative_path in files:
                    archive.write(
                        os.path.join(root, relative_path),
                        os.path.join(relative_root, relative_path))

        return archive_path

    @classmethod
    def fetch_addon_from_git(cls, addon_path, target_folder):

        match = re.match(r'((?:[A-Za-z0-9+.-]+://)?.*?)(?:#([^#]*?))?(?::([^:]*))?$', addon_path)
        clone_repo, clone_branch, clone_path_option = match.group(1, 2, 3)
        clone_path = (cls.get_posix_path(os.path.join('.', ''))
                      if clone_path_option is None else clone_path_option)

        clone_folder = tempfile.mkdtemp('-repo')
        try:
            cloned = git.Repo.clone_from(clone_repo, clone_folder)
            if clone_branch is not None:
                cloned.git.checkout(clone_branch)
            source_folder = os.path.join(clone_folder, clone_folder)
            metadata_path = os.path.join(source_folder, clone_path, cls.__INFO_BASENAME)
            metadata = cls.parse_metadata(metadata_path)
            target_folder = os.path.join(target_folder, metadata.id)

            archive_path = cls.create_git_archive(target_folder, metadata, clone_path, cloned)
            cls.generate_checksum(archive_path)
            cls.copy_metadata_files(source_folder, target_folder, metadata)

            return metadata
        finally:
            shutil.rmtree(
                clone_folder,
                ignore_errors=False,
                onerror=cls.on_remove_error)

    @classmethod
    def on_remove_error(cls, function, path, excinfo):
        exc_info_value = excinfo[1]
        if (hasattr(exc_info_value, 'errno') and
                exc_info_value.errno == errno.EACCES):
            os.chmod(path, stat.S_IWUSR)
            function(path)
        else:
            raise

    @classmethod
    def fetch_addon_from_folder(cls, addon_path, target_folder):
        addon_path = os.path.expanduser(addon_path)
        metadata_path = os.path.join(addon_path, cls.__INFO_BASENAME)
        metadata = cls.parse_metadata(metadata_path)
        target_folder = os.path.join(target_folder, metadata.id)

        archive_path = cls.create_folder_archive(target_folder, metadata, addon_path)

        cls.generate_checksum(archive_path)

        if not os.path.samefile(addon_path, target_folder):
            cls.copy_metadata_files(addon_path, target_folder, metadata)

        return metadata

    @classmethod
    def fetch_addon_from_zip(cls, addon_path, target_folder):
        addon_path = os.path.expanduser(addon_path)
        with zipfile.ZipFile(addon_path, compression=zipfile.ZIP_DEFLATED) as archive:
            roots = frozenset(
                next(iter(path.split(os.path.sep)), '')
                for path in archive.namelist())

            if len(roots) != 1:
                raise RuntimeError('Archive should contain one directory')
            root = next(iter(roots))

            metadata_file = archive.open(os.path.join(root, cls.__INFO_BASENAME))
            metadata = cls.parse_metadata(metadata_file)
            target_folder = os.path.join(target_folder, metadata.id)

            if not os.path.isdir(target_folder):
                os.mkdir(target_folder)
            for (source_basename, target_basename) in cls.get_metadata_basenames(metadata):
                try:
                    source_file = archive.open(os.path.join(root, source_basename))
                except KeyError:
                    continue
                with open(
                        os.path.join(target_folder, target_basename),
                        'wb') as target_file:
                    shutil.copyfileobj(source_file, target_file)

        archive_basename = cls.get_archive_basename(metadata)
        archive_path = os.path.join(target_folder, archive_basename)
        if (not os.path.samefile(
                os.path.dirname(addon_path), target_folder) or
                os.path.basename(addon_path) != archive_basename):
            shutil.copyfile(addon_path, archive_path)

        info_path = cls.get_info_path(archive_path)
        checksum_path = cls.get_checksum_path(info_path)
        cls.generate_checksum(checksum_path)

        return metadata

    @classmethod
    def fetch_addon(cls, addon_path, target_folder, result_slot):
        try:
            if cls.is_url(addon_path):
                metadata = cls.fetch_addon_from_git(addon_path, target_folder)

            elif os.path.isdir(addon_path):
                metadata = cls.fetch_addon_from_folder(addon_path, target_folder)

            elif os.path.isfile(addon_path):
                metadata = cls.fetch_addon_from_zip(addon_path, target_folder)

            else:
                raise RuntimeError('Path not found: {}'.format(addon_path))

            result_slot.append(cls.__worker_result(metadata, None))
        except:
            result_slot.append(cls.__worker_result(None, sys.exc_info()))

    @classmethod
    def get_addon_worker(cls, addon_path, target_folder):
        result_slot = []
        thread = threading.Thread(target=lambda: cls.fetch_addon(addon_path, target_folder, result_slot))
        return cls.__addon_worker(thread, result_slot)

    @classmethod
    def import_git(cls, paths):

        if any(cls.is_url(path) for path in paths):
            try:
                global git
                import git
            except ImportError:
                raise RuntimeError(
                    'Please install GitPython: pip install gitpython')

    @classmethod
    def create_repository(
            cls,
            addon_paths,
            target_folder,
            info_path,
            checksum_path=None,
            is_compressed=False):

        cls.import_git(addon_paths)

        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)

        workers = [
            cls.get_addon_worker(addon_path, target_folder)
            for addon_path in addon_paths]

        for worker in workers:
                worker.thread.run()

        metadata = []
        for worker in workers:
            try:
                result = next(iter(worker.result_slot))
            except StopIteration:
                raise RuntimeError('Addon worker did not report result')
            if result.exc_info is not None:
                raise result.exc_info[1]
            metadata.append(result.metadata)

        root = xml.etree.ElementTree.Element('addons')
        for addon_metadata in metadata:
            root.append(addon_metadata.root)
        tree = xml.etree.ElementTree.ElementTree(root)
        if is_compressed:
            info_file = gzip.open(info_path, 'wb')
        else:
            info_file = open(info_path, 'wb')
        with info_file:
            tree.write(info_file, encoding='UTF-8', xml_declaration=True)
        is_binary = is_compressed
        cls.generate_checksum(info_path, is_binary, checksum_path)
    
    @classmethod
    def create(cls,output_folder, addon_paths, is_compressed=False, ):
        output_folder = os.path.expanduser(output_folder)
        info_path = cls.get_info_path(output_folder, is_compressed, True)
        checksum_path = "{}.md5".format(info_path)
        cls.create_repository( addon_paths, output_folder, info_path, checksum_path, is_compressed)

    @classmethod
    def get_info_path(cls, folder_path, is_compressed= False, addons=False):
        info_basename = "addons.xml" if addons else "addon.xml"
        info_basename += ".gz" if is_compressed else ""

        return os.path.join(folder_path, info_basename)

   
if __name__ == "__main__":
    main()