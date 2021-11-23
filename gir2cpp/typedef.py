import abc


class TypeDef:

    @abc.abstractmethod
    def output(self, ns_dir):
        raise NotImplementedError()

    @abc.abstractmethod
    def cast_from_c(self, varname):
        raise NotImplementedError()

    @abc.abstractmethod
    def cast_to_c(self, varname, refctype):
        raise NotImplementedError()

    @abc.abstractmethod
    def cpp_type(self, decl):
        raise NotImplementedError()
