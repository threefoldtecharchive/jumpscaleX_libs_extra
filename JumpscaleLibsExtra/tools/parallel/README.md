# parallel

tool to help executing multiple tasks concurrently within gevent context

## Examples

### Simple

```python
    def test_simple(self):
        "kosmos -p 'j.tools.parallel.test()'"
        def sleepf(howlong, name="fun"):
            print("{} is sleeping for {}".format(name, howlong))
            for i in range(howlong):
                print("{} is sleeping slept for {}".format(name, howlong-i))
                gevent.sleep(i)

        for i in range(5):
            self.add_task(sleepf, i, name="fun{}".format(i))

        self.run()
```

### Getting results of the execution

```python

    def test_with_results(self):
        "kosmos -p 'j.tools.parallel.test_with_results()'"
        def sleepf(howlong, name="fun"):
            print("{} is sleeping for {}".format(name, howlong))
            for i in range(howlong):
                print("{} is sleeping slept for {}".format(name, howlong-i))
                gevent.sleep(i)
            return 7

        for i in range(5):
            self.add_task(sleepf, i, name="fun{}".format(i))

        greenlets = self.run()
        results = [greenlet.value for greenlet in greenlets ]
        assert all(map(lambda x: x==7, results)) == True
        print(results)

```



### One of the tasks may raise an error

```python
    def test_with_errors(self):
        "kosmos -p 'j.tools.parallel.test_with_errors()'"
        def sleepf(howlong, name="fun"):
            print("{} is sleeping for {}".format(name, howlong))
            for i in range(howlong):
                print("{} is sleeping slept for {}".format(name, howlong-i))
                gevent.sleep(i)

        def sleepf_with_error(howlong, name="fun"):
            print("{} is sleeping for {}".format(name, howlong))
            for i in range(howlong):
                print("{} is sleeping slept for {}".format(name, howlong-i))
                gevent.sleep(i)
            raise RuntimeError("error here in sleepf_with_error")


        for i in range(5):
            self.add_task(sleepf, i, name="fun{}".format(i))

        self.add_task(sleepf_with_error, i, name="error_fun")

        self.run()

```

