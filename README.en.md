# TinyServer

#### 1. Description
​		Local Python projects run the basic framework, no need to install third party libraries, built-in pure Python native implementation of multiprocess HTTP server, through the built-in RESTful Web API or web page to view the local log, can be timed to execute code, can be notifications, can define server API to view the running status, Customizable Web templates.

#### 2. Key Feature
- Provides logging, configuration management for running Python projects on the server
- Web page view log
- RESTful APIs provide an interface to project information

- Periodically execute the module, executing /Core/main.py on a regular basis based on the start and end time
- Message notification module, send email or cooperate with Mirai framework to send QQ messages
- Server API
- Program information and system status can be queried through the built-in API
- Customizable simple API
- Custom web templates

#### 3. Basic Modules

- Core
- main. py - Entry to program execution
- Config
  - config.ini - Fill in the basic configuration information
  - settings.py - Read and initialize data in config.ini
- Logger
- logger - Outputs log messages to the console, log file, and Server module
- Message
- message - Message passing interface, can send messages through QQ robot and mailbox
- Scheduler
  - Scheduler - Scheduled execution of the /Core/main.py module. Once opened and set in config.ini, the /Core/main.py module is scheduled to be executed
- Server
- Handler - Contains the main HTTP request handling and API
- server - Used to configure and start the server thread
- Static
- Web page view log
- RESTful APIs provide an interface to project information

#### 4. Operation Environment

- [Python 3](https://www.python.org/)

#### 5. Installation Tutorial

1. ```shell
   git clone https://gitee.com/louisyoung1/tiny-server.git
   ```

2. ```sh
   cd tiny-server
   ```


#### 6. Usage

1. Change the code in /Core/main.py to the code you want to run

2. Edit the configuration items in /Config/config.ini file according to the comment requirements

3. Make sure you are in /tiny-server and enter

   ```sh
   python3 runserver
   ```

#### 7. Directory Structure

```shell
.
├── Config
│   ├── config.ini
│   └── settings.py
├── Core
│   └── core.py
├── Logger
│   ├── Log_Files
│   │   └── TinyServer.log
│   └── logger.py
├── Message
│   └── message.py
├── Scheduler
│   ├── scheduler.py
│   └── tools.py
├── Server
│   ├── handler.py
│   └── server.py
├── Static
│   ├── 404.html
│   ├── change.html
│   ├── css
│   ├── favicon.ico
│   ├── images
│   ├── index.html
│   ├── js
│   └── log.html
└── runserver.py
```

#### 8. Contribution

1.  Fork the repository
2.  Create Feat_xxx branch
3.  Commit your code
4.  Create Pull Request
