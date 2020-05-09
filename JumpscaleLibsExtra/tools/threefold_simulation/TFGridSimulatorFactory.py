from Jumpscale import j

from .TFGridSimulator import TFGridSimulator
from .BillOfMaterial import Environment, BillOfMaterial
import sys
from .SimulatorConfig import SimulatorConfig

f = j.core.text.format_item
import gevent
import gipc

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
        growth = None,
        reload=True,
        token_price = None,
        log=False,
        export=False,
        cloudunits_price_range=None
    ):
        """
        example how to use

        ```
        simulation = j.tools.tfgrid_simulator.simulation_get(growth=1000000)
        ```

        @param growth: amount of servers the grid will have in 2025
            accepted inputs: 50000,100000,200000,600000,1000000,2000000,4000000,10000000

        @param token_price: what will the token price be in 5 years from now?
            accepted inputs: 0.15,0.3,0.6,1,2,3,6,10,20,40,100,500,auto

        @param cloudunits_price_range: 1,2,3,4
            1:
                CU: 10
                SU: 6
                NU: 0.04
            2:
                CU: 12
                SU: 8
                NU: 0.05
            3:
                CU: 15
                SU: 10
                NU: 0.05
            4:
                CU: 20
                SU: 15
                NU: 0.08


        @param keep, means we simulate and store the result

        """

        config = self.simulator_config

        if not node_growth:

            if not growth:
                growth = config.node_growth

            assert isinstance(growth,int)
            if not growth in [50000,100000,200000,600000,1000000,2000000,4000000,10000000]:
                raise j.exceptions.Input(f"growth needs to be in: 50000,100000,200000,600000,1000000,2000000,4000000,10000000,20000000, now {growth}")

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
                node_growth = "0:5,6:150,12:2000,18:16000,24:38000,48:52000,60:60000"
            elif growth == 4000000:
                node_growth = "0:5,6:150,12:3000,18:25000,24:67000,48:110000,60:130000"
            elif growth == 10000000:
                node_growth = "0:5,6:150,12:4000,18:40000,24:120000,48:300000,60:440000"
            else:
                node_growth = "0:5,6:150,20:2000"
        else:
            node_growth = "0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000"

        if token_price:
            assert isinstance(token_price, int) or isinstance(token_price, float) or isinstance(token_price, str)
            if isinstance(token_price, str) and token_price == "auto":
                config.tft_price_5y = 0
                config.tft_pricing_type = "auto"
            else:
                if token_price not in [0.15,0.3,0.6,1,2,3,6,10,20,40,100,500]:
                    raise j.exceptions.Input(f"price needs to be in: 0.15,0.3,0.6,1,2,3,6,10,20,40,100,500 now:{token_price }")
                config.tft_price_5y = token_price


        if cloudunits_price_range:
            if cloudunits_price_range==1:
                config.pricing.price_cu = 10
                config.pricing.price_su = 6
                config.pricing.price_nu = 0.04
            elif cloudunits_price_range==2:
                config.pricing.price_cu = 12
                config.pricing.price_su = 8
                config.pricing.price_nu = 0.05
            elif cloudunits_price_range==3:
                config.pricing.price_cu = 15
                config.pricing.price_su = 10
                config.pricing.price_nu = 0.05
            elif cloudunits_price_range==4:
                config.pricing.price_cu = 20
                config.pricing.price_su = 15
                config.pricing.price_nu = 0.08
            else:
                raise j.exceptions.Input(f"cloudunits_price_range needs to be in: 1,2,3,4 now:{cloudunits_price_range}")

            config.cloudunits_price_range = cloudunits_price_range

            config.cloudvaluation.price_cu=config.pricing.price_cu
            config.cloudvaluation.price_su=config.pricing.price_su
            config.cloudvaluation.price_nu=config.pricing.price_nu

        if log:
            print(f" - tft_price_5y: {config.tft_price_5y}")
            print(f" - node_growth: {node_growth}")
            if growth:
                print(f" - growth: {f(growth)}")

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

            if log:
                print(f" - price_cu: {config.pricing.price_cu}")
                print(f" - price_su: {config.pricing.price_su}")
                print(f" - price_nu: {config.pricing.price_nu}")

            # we need the simulator to add the batches automatically based on chosen environment
            simulation.nodesbatches_add_auto(environment=environment)
            # put the default bom's
            simulation.environment = environment
            simulation.bom = environment.bom
            simulation.config = config

            self._instances[name] = simulation

        simulation = self._instances[name]

        if log:
            print(f" - nr nodes in 5 years: {f(simulation.rows.nrnodes_total.cells[60])}")

        simulation.calc()
        if export:
            if not growth:
                growth = node_growth
            if not cloudunits_price_range:
                cloudunits_price_range = f"{config.pricing.price_cu}_{config.pricing.price_su}_{config.pricing.price_nu}"
            exportpath = "{DIR_HOME}/code/github/threefoldfoundation/simulator_export/tfsimulator/export"
            price5y=config.tft_price_5y
            if price5y==0:
                price5y = "auto"
            exportpath2 = f"{exportpath}/{hardware_config_name}/{growth}/tft_{price5y}/price_{int(cloudunits_price_range)}"
            exportpath2 = j.core.tools.text_replace(exportpath2)
            j.core.tools.dir_ensure(exportpath2)
            simulation.markdown_export(exportpath2)

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

    def environment_get(self, name="amd", reload=True):
        """
        name is name of file in notebooks/params/hardware

        ```
        simulation = j.tools.tfgrid_simulator.bom_get()
        ```

        return (bom,environment)

        """
        if reload or name not in self._environments:
            # if reload or name not in self._bom:
            environment = Environment(name=name)
            self._environments[name] = environment
        return self._environments[name]

    def calc(self, growth=None, token_price=None, cloudunits_price_range=None, reload=True,export=True):
        """
        kosmos 'j.tools.tfgrid_simulator.calc(export=True)'
        kosmos 'j.tools.tfgrid_simulator.calc(reload=True)'


        @param growth: amount of servers the grid will have in 2025
            accepted inputs: 50000,100000,200000,600000,1000000,2000000,4000000,10000000,20000000

        @param token_price: what will the token price be in 5 years from now?
            accepted inputs: 0.15,0.3,0.6,1,2,3,6,10,20,40,100,500,auto

        @param cloudunits_price_range: 1,2,3,4

            1:
                CU: 10
                SU: 6
                NU: 0.04
            2:
                CU: 12
                SU: 8
                NU: 0.05
            3:
                CU: 15
                SU: 10
                NU: 0.05
            4:
                CU: 20
                SU: 15
                NU: 0.08

        @param export, if True will write the results of the simulation in a directory so it can be used for visualization purposes

        :return:
        """

        startmonth = 1



        simulation = self.simulation_get(growth=growth,token_price=token_price,
            cloudunits_price_range=cloudunits_price_range,
            name="default", tokencreator_name="optimized", hardware_config_name="amd", reload=reload,log=True,export=export
        )

        # nb0 = simulation.nodesbatch_get(startmonth)
        # # nb0.graph("cost_network")
        #
        # print(simulation)
        # print(nb0)
        #
        # print(nb0.markdown_profit_loss(10))
        # print(nb0.markdown_profit_loss(10))

        return simulation

    def markdown_export(self,all=False,one=False,debug=False):
        """
        kosmos 'j.tools.tfgrid_simulator.markdown_export()'
        kosmos 'j.tools.tfgrid_simulator.markdown_export(debug=True)'
        kosmos 'j.tools.tfgrid_simulator.markdown_export(one=True)'
        """


        schedule_q = gevent.queue.Queue()

        def server(schedule_q):
            processes = j.baseclasses.dict()
            max_processes = 6
            while True:
                if len(processes)<max_processes and schedule_q.qsize()>0:
                    growth, token_price, cloudunits_price_range = schedule_q.get()
                    print(f" - schedule  {growth}, {token_price}, {cloudunits_price_range}")
                    name = f" {growth}_{token_price}_{cloudunits_price_range}"
                    kwargs={"growth":growth,"token_price":token_price,"cloudunits_price_range":cloudunits_price_range}
                    p = gipc.start_process(target=self.calc, kwargs=kwargs,name=name)
                    processes[name]=p
                for p in [p for p in processes.values()]:
                    if p.is_alive():
                        continue
                    else:
                        if p.exitcode!=0:
                            # print("CANNOT EXECUTE")
                            raise j.exceptions.Base("could not execute:%"%p.name)

                        processes.pop(p.name)

                if schedule_q.qsize()==0 and len(processes)==0:
                    return

                gevent.sleep(1)
                print(f" - nr processes: {len(processes)} : remaining: {schedule_q.qsize()}")
                # print(f" - nr processes: {len(p)}")

        if all:
            for growth in [50000,100000,200000,600000,1000000,2000000,4000000,10000000,20000000]:
                for token_price in [0.15,0.3,0.6,1,2,3,6,10,20,40,100,500,"auto"]:
                    for cloudunits_price_range in [1,2,3,4]:
                        schedule_q.put((growth, token_price, cloudunits_price_range))
        elif one:
            growth=1000000
            token_price="auto"
            cloudunits_price_range = 2
            self.calc(growth, token_price, cloudunits_price_range)
        else:
            for growth in [100000,1000000,4000000]:
                for token_price in ["auto",0.3,3]:
                    for cloudunits_price_range in [1,3]:
                        if debug:
                            self.calc(growth, token_price, cloudunits_price_range)
                        else:
                            schedule_q.put((growth, token_price, cloudunits_price_range))

        s=gevent.spawn(server,schedule_q)
        s.join()

        print ("ALL SIMULATIONS DONE !!!")


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
