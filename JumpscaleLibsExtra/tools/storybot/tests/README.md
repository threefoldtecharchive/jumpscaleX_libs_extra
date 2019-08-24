## StoryBot testsuite

###  Install requirements
```bash
git clone https://github.com/Jumpscale/lib
cd lib/JumpscaleLib/tools/storybot/tests
pip3 install -r requirements.txt
```

### Set configuration
set configuration in config.ini
```ini
[Github]
token = # github token
```
> Make sure to select **delete_repo** scope when you generate your github token to automatically clean up the created repos during the tests.

### Run tests
```bash
nosetests -s -v --logging-level=WARNING tests.py --tc-file config.ini
```
