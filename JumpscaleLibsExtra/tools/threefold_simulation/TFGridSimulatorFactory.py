from Jumpscale import j

from .TFGridSimulator import TFGridSimulator
from .BillOfMaterial import Environment, BillOfMaterial
import sys


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

    def simulation_get(
        self,
        name="default",
        tokencreator_name="optimized",
        hardware_config_name="amd",
        node_growth=None,
        tft_growth=None,
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
        if not tft_growth:
            if j.core.db.get("simulator:price"):
                tft_growth = float(j.core.db.get("simulator:price").decode())
                if tft_growth == 0:
                    tft_growth = "auto100"
            else:
                tft_growth = 3

        if not node_growth:
            if j.core.db.get("simulator:node_growth"):
                growth = int(j.core.db.get("simulator:node_growth").decode())
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

        print(f" - tft_growth: {tft_growth}")
        print(f" - node_growth: {node_growth}")

        if reload or name not in self._instances:
            simulation = TFGridSimulator(name=name)
            # choose your token simulation !!!
            environment = self.environment_get(hardware_config_name, reload=reload)
            assert environment.nr_devices > 0

            exec(f"from token_creators.{tokencreator_name} import TokenCreator", globals())
            simulation.token_creator = TokenCreator(simulation=simulation, environment=environment)

            exec(f"from simulations.{name} import simulation_calc", globals())
            simulation, environment = simulation_calc(simulation, environment)

            # if tft_growth:
            simulation.tokenprice_set(tft_growth)

            # if node_growth:
            simulation.nrnodes_new_set(node_growth)

            cu_price_default = 8
            su_price_default = 5
            if j.core.db.get("simulator:cu_price"):
                cu_price_default = int(j.core.db.get("simulator:cu_price").decode())
            if j.core.db.get("simulator:su_price"):
                su_price_default = int(j.core.db.get("simulator:su_price").decode())
            simulation.sales_price_cu = f"{cu_price_default} USD"
            # storage unit = 1 TB of netto usable storage, in market prices between 20 and USD120
            simulation.sales_price_su = f"{su_price_default} USD"

            print(f" - cu_price_default: {cu_price_default}")
            print(f" - su_price_default: {su_price_default}")

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

        startmonth = 0

        # define how the nodes will grow
        # node_growth = "0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000"
        # node_growth="0:5,6:150,12:1000,24:5000"
        # node_growth="0:1000"
        node_growth = None

        # tft price in 5 years, has impact on return
        # tft_price = 3
        # tft_price = "0:0.15"
        tft_price = None

        simulation = j.tools.tfgrid_simulator.simulation_get(
            name="default",
            tokencreator_name="optimized",
            hardware_config_name="amd",  # dont change here, this is the growth calc
            node_growth=node_growth,
            tft_growth=tft_price,
            reload=True,
        )

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

        j.shell()

        # print(nb.normalized)

        print(nb.tft_farmed_total)

        # nb._values_usd_get()

        nb.graph_tft(single=True)

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

    def calc(self, batches_simulation=False, reload=False):
        """
        kosmos 'j.tools.tfgrid_simulator.calc()'
        kosmos 'j.tools.tfgrid_simulator.calc(reload=True)'
        :return:
        """

        startmonth = 1

        simulation = self.simulation_get(
            name="default", tokencreator_name="optimized", hardware_config_name="amd", reload=reload
        )

        nb0 = simulation.nodesbatch_get(0)

        print(simulation)
        print(nb0)

        j.shell()
        nb0.tft_farmed_total

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
        background=False,
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

        if background:
            startup = j.servers.startupcmd.get(name="simulator", cmd_start="j.tools.tfgrid_simulator.start()")
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

    def stop(
        self, voila=False, background=False, base_url=None, name=None, pname="notebook", path_source=None, reset=False
    ):
        path_dest = self.get_path_dest(name=name, path_source=path_source, reset=reset)
        j.servers.notebook.stop(path=path_dest, voila=voila, background=background, base_url=base_url, pname=pname)
