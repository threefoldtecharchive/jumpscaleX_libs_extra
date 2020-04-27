from Jumpscale import j

from .TFGridSimulator import TFGridSimulator
from .BillOfMaterial import Environment, BillOfMaterial
import sys
from .SimulatorConfig import SimulatorConfig


class TFGridSimulatorFactory(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfgrid_simulator"

    def _init(self, **kwargs):
        j.application.start("simulator")
        self._instances = j.baseclasses.dict()
        self._environments = j.baseclasses.dict()
        self._bom = j.baseclasses.dict()

        notebookpath = j.core.tools.text_replace(
            "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks"
        )
        if notebookpath not in sys.path:
            sys.path.append(notebookpath)

        self.simulator_config = SimulatorConfig()

    @property
    def default(self):
        s = self.simulation_get("default")
        return s

    def hardware_platform_choices(self):
        return [
            j.sal.fs.getBaseName(i)[:-3]
            for i in j.sal.fs.listFilesInDir(self._dirpath + "/notebooks/hardware")
            if j.sal.fs.getFileExtension(i) == "py"
        ]

    def _code_links_create(self):
        """
        create the links to code so its visible from the notebook

        kosmos 'j.tools.tfgrid_simulator.code_links_create()'

        """
        src = f"{self._dirpath}"
        dest = f"{self._dirpath}/notebooks/code/"
        j.core.tools.delete(dest)
        j.sal.fs.symlinkFilesInDir(src, dest, delete=False, includeDirs=False, makeExecutable=False, filter="*.py")

    def simulation_get(
        self,
        name="default",
        tokencreator_name="optimized",
        hardware_config_name="amd",
        node_growth=None,
        reload=True,
        calc=True,
    ):
        """
        example how to use

        ```
        simulation = j.tools.tfgrid_simulator.simulation_get()
        ```

        @param node_growth: if empty will be whatever was defined in the simlator name see notebooks/simulators
            default: "0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000"
        @param tft_growth: if empty will be whatever was defined in the simlator name see notebooks/simulators
            default: "0:0.15,60:3"

        ## meaning of the interpolation values
        # 0:0 means month 0 we have value 0
        # 60:3 means month 60: value is 3
        # interpolation will happen between the values
        # above: the price go from 0.15 first month to 3 over 60 months


        """
        config = self.simulator_config

        if not node_growth:
            growth = config.node_growth
            if growth == 50000:
                node_growth = "0:5,6:150,20:1000"
            elif growth == 100000:
                node_growth = "0:5,6:150,20:2000"
            elif growth == 200000:
                node_growth = "0:5,6:150,12:1000,18:2000,24:4800"
            elif growth == 600000:
                node_growth = "0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000"
            elif growth == 1000000:
                node_growth = "0:5,6:150,12:1000,18:6000,24:12000,48:34000,60:34000"
            elif growth == 2000000:
                node_growth = "0:5,6:150,12:2000,18:16000,24:36000,48:60000,60:60000"

            else:
                node_growth = "0:5,6:150,20:2000"
        else:
            node_growth = "0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000"

        print(f" - tft_price_5y: {config.tft_price_5y}")
        print(f" - node_growth: {node_growth}")

        if reload or name not in self._instances:
            simulation = TFGridSimulator(name=name)
            # choose your token simulation !!!
            environment = self.environment_get(hardware_config_name, reload=reload)
            assert environment.nodes_production_count > 0

            exec(f"from token_creators.{tokencreator_name} import TokenCreator", globals())
            simulation.token_creator = TokenCreator(simulation=simulation, environment=environment)

            exec(f"from simulations.{name} import simulation_calc", globals())
            simulation, environment = simulation_calc(simulation, environment)

            environment.calc()

            # if node_growth:
            simulation.nrnodes_new_set(node_growth)

            print(f" - price_cu: {config.pricing.price_cu}")
            print(f" - price_su: {config.pricing.price_su}")
            print(f" - price_nu: {config.pricing.price_nu}")

            # we need the simulator to add the batches automatically based on chosen environment
            simulation.nodesbatches_add_auto(environment=environment)
            # put the default bom's
            simulation.environment = environment
            simulation.bom = environment.bom

            self._instances[name] = simulation

        simulation = self._instances[name]

        simulation.calc()
        # calc = True
        # if calc and simulation.simulated == False:
        #     key = f"{name}_{tokencreator_name}_{hardware_config_name}_{node_growth}_{tft_growth}"
        #     simulation.import_redis(key=key, autocacl=True, reset=reload)

        return simulation

    def calc_custom_environment(self, reload=False):
        """
        kosmos 'j.tools.tfgrid_simulator.calc_custom_environment()'
        kosmos 'j.tools.tfgrid_simulator.calc_custom_environment(reload=True)'
        """

        startmonth = 1

        simulation = j.tools.tfgrid_simulator.simulation_get(tokencreator_name="optimized", reload=True,)

        ###################################################
        ## NOW THE NODES BATCH WE WANT TO SIMULATE FOR

        # bill of material name
        # hardware_config_name = "CH_archive"
        hardware_config_name = "A_dc_rack"
        # hardware_config_name = "hpe_dl385_amd"
        # hardware_config_name = "amd"

        # parameters for simulation
        # choose your hardware profile (other choices in stead of amd or supermicro or hpe)
        nb = simulation.nodesbatch_simulate(month=startmonth, hardware_config_name=hardware_config_name)

        print(nb)
        print(nb.node_normalized)

        # nb.graph_tft(single=True)

        print(nb.roi_end)

    def environment_get(self, name="amd", reload=False):
        """
        name is name of file in notebooks/params/hardware

        ```
        simulation = j.tools.tfgrid_simulator.bom_get()
        ```

        return (bom,environment)

        """
        if not reload or name not in self._environments:
            # if reload or name not in self._bom:
            environment = Environment(name=name)
            self._environments[name] = environment
        return self._environments[name]

    def calc(self, batches_simulation=False, reload=False, detail=False):
        """
        kosmos 'j.tools.tfgrid_simulator.calc()'
        kosmos 'j.tools.tfgrid_simulator.calc(reload=True)'
        :return:
        """

        startmonth = 1

        simulation = self.simulation_get(
            name="default", tokencreator_name="optimized", hardware_config_name="amd", reload=reload
        )

        nb0 = simulation.nodesbatch_get(startmonth)
        if detail:
            nb0.calc(detail=True)

        # nb0.graph("cost_network")

        print(simulation)
        print(nb0)

        print(nb0.markdown_profit_loss(10))
        print(nb0.markdown_profit_loss(10))

        j.shell()

        return

    def get_path_dest(self, name=None, path_source=None, reset=False):
        if not path_source:
            path_source = "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/home.ipynb"
        path_source = j.core.tools.text_replace(path_source)
        if name:
            path_dest = j.core.tools.text_replace("{DIR_VAR}/notebooks/%s" % name)
            if reset:
                j.core.tools.remove(path_dest)
            j.sal.fs.copyDirTree(path_source, path_dest, overwriteFiles=False)
        else:
            path_dest = path_source
        return path_dest

    def start(
        self,
        voila=False,
        background=True,
        base_url=None,
        name=None,
        port=8888,
        pname="notebook",
        path_source=None,
        reset=False,
    ):
        """
        to run:

        kosmos -p 'j.tools.tfgrid_simulator.start()'

        #means we run the notebook in the code env (careful)
        kosmos -p 'j.tools.tfgrid_simulator.start(name=None)'
        """

        self._code_links_create()

        if background:
            if base_url:
                cmd_start = f"j.tools.tfgrid_simulator.start(port={port},background=False, base_url='{base_url}')"
            else:
                cmd_start = f"j.tools.tfgrid_simulator.start(port={port},background=False)"
            startup = j.servers.startupcmd.get(name="simulator", cmd_start=cmd_start)
            startup.interpreter = "jumpscale"
            startup.timeout = 60
            startup.ports = [port]
            startup.start()
        else:
            j.application.start("tfsimulation")

            j.core.myenv.log_includes = []
            # e = self.calc()
            path_dest = self.get_path_dest(name=name, reset=reset, path_source=path_source)
            self._log_info("start notebook on:%s" % path_dest)

            j.servers.notebook.start(
                path=path_dest, voila=voila, background=background, base_url=base_url, port=port, pname=pname
            )  # it will open a browser with access to the right output
            j.application.reset_context()

    def stop(self):
        startup = j.servers.startupcmd.get(name="simulator")
        startup.stop()
