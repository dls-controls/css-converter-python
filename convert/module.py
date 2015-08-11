import os
import utils
import dependency


def convert(origin, destination):
    pass


class Module(object):

    def __init__(self, name, version, prod_root, mirror_root, is_ioc=True):
        self.area = 'ioc' if is_ioc else 'support'
        self.prod_root = prod_root
        self.module_dir = os.path.join(self.prod_root, self.area, name)
        if not os.path.exists(self.module_dir):
            raise ValueError('Cannot locate module {} at {}'.format(name, self.module_dir))

        self.mirror_root = mirror_root
        self.name = name
        self.old_version = version
        self.new_version = utils.increment_version(self.old_version)
        self.deps = []

    def get_dependencies(self):
        print(self.name, self.old_version)
        dp = dependency.DependencyParser(self.prod_root, self.area,
                                         self.name, self.old_version)
        deps = dp.find_dependencies()
        for d in deps:
            version = deps[d][1]
            self.deps.append(Module(d, version, self.prod_root, self.mirror_root, False))

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
