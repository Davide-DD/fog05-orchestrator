class Architecture:

    ######################### BEGIN ARCHITECTURE LIFECYCLE #######################

    def configure(self,configuration):
        raise NotImplementedError()

    def associate(self,fog05_api,environment,args):
        raise NotImplementedError()

    def deploy(self,data=None):
        raise NotImplementedError()

    def serve(self,data=None):
        raise NotImplementedError()

    def undeploy(self):
        raise NotImplementedError()

    ########################### END ARCHITECTURE LIFECYCLE #######################


    ############################## BEGIN UTILITY METHODS #########################

    def check_status(self):
        raise NotImplementedError()

    def __get_requirements(self,operation):
        raise NotImplementedError()

    def get_mapping(self,operation='deploy'):
        raise NotImplementedError()

    ################################ END UTILITY METHODS #########################