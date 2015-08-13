import utils
import files
import os
import shutil
import dependency
import coordinates
import paths


def convert(origin, destination):
    pass


class Module(object):

    def __init__(self, coords, mirror_root):
        self.coordinates = coords
        self.old_version = coords.version
        self.module_dir = coordinates.as_path(coords, False)
        if not os.path.exists(self.module_dir):
            raise ValueError('Cannot locate module {} at {}'.format(coords.name,
                                                                    self.module_dir))

        self.mirror_root = mirror_root
        self.new_version = utils.increment_version(self.old_version)
        self.deps = []

    def get_dependencies(self):
        dp = dependency.DependencyParser(self.coordinates)
        self.deps = dp.find_dependencies()

    def get_dependency_file_dict(self):
        all_files = {}
        for dep in self.deps:
            all_files.update(dep.get_file_dict())

    def get_file_dict(self):
        # For all files return a dictionary {filename: path-within-module}
        # This allows us to find any edl file by name
        return {}

    def convert(self, data='data', opi='opi/opi'):
        origin = os.path.join(self.module_dir, self.old_version, data)
        destination = os.path.join(self.mirror_root, self.module_dir,
                                   self.new_version, self.name + 'App', opi)
        convert(origin, destination)
