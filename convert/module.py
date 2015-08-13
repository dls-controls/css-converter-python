import os
import utils
import dependency


def convert(origin, destination):
    pass


class Module(object):

    def __init__(self, coords, mirror_root):
        self.name = coords.module
        self.area = coords.area
        self.old_version = coords.version
        self.prod_root = coords.root
        self.module_dir = os.path.join(self.prod_root, self.area, self.name)
        if not os.path.exists(self.module_dir):
            raise ValueError('Cannot locate module {} at {}'.format(self.name,
                                                                    self.module_dir))

        self.mirror_root = mirror_root
        self.new_version = utils.increment_version(self.old_version)
        self.deps = []

    def get_dependencies(self):
        print(self.name, self.old_version)
        dp = dependency.DependencyParser(self.prod_root, self.area,
                                         self.name, self.old_version)
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
