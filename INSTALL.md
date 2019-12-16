# clubpromoters-api
Set up the live version, and a test version of the clubpromoters-api.



## Installation (Ubuntu 18.04 LTS)

### Preparation


#### Mail
Before installing the cluster, it is advised you install the mailserver repository first, found at: [https://github.com/AlenAlic/mailserver](https://github.com/AlenAlic/mailserver) 

This will configure the server to be able to send and receive mail, something that the clubpromoters-api needs. 

Follow the instructions there, then come back here.


#### DNS settings
In general, TLL values of 5 Min. (300 sec) are recommended.

Make sure you have the following DNS records available:

|Name|Type|Value|INFO|
|---|---|---|---|
|@|A|\<your ipv4 adress\>|
|@|AAAA|\<your ipv6 adress\>|
|api|CNAME|@|
|test.api|CNAME|@|



### Installer instance
We'll use an instance of the xTDS WebPortal to install the cluster.

    git clone https://github.com/AlenAlic/clubpromoters-api
    cd clubpromoters-api
    
From here you can run any of the installations located in the scripts folder.



### Variables
Before installing anything, set the following environment variables:

    export FLASK_APP=run.py
    export DOMAIN=clubpromoters.net



### Installation scripts

#### Base items
To install all the base dependencies, run the `install_base` script.

    source scripts/install_base


#### LIVE
Before installing the ETDS version, set the following environment variables:

    export LIVE_EMAIL_PASSWORD=<password>
    export LIVE_DB_PASSWORD=$(python3 -c "import uuid; print(uuid.uuid4().hex)")
    export LIVE_SECRET_KEY=$(python3 -c "import uuid; print(uuid.uuid4().hex)")
    export LIVE_FOLDER=LIVE
Then run the installation script:

    source scripts/install_LIVE
Finally, copy the `LIVE_DB_PASSWORD` and run the following command to create a login path for cronjobs to run backups:

    sudo mysql_config_editor set --login-path=clubpromoters_live --host=localhost --user=clubpromoters_live --password
When prompted, paste the password and press Enter.
 
#### TEST
Before installing the NTDS version, set the following environment variables:

    export TEST_EMAIL_PASSWORD=<password>
    export TEST_DB_PASSWORD=$(python3 -c "import uuid; print(uuid.uuid4().hex)")
    export TEST_SECRET_KEY=$(python3 -c "import uuid; print(uuid.uuid4().hex)")
    export TEST_FOLDER=TEST
Then run the installation script:

    source scripts/install_TEST
Finally, copy the `TEST_DB_PASSWORD` and run the following command to create a login path for cronjobs to run backups:

    sudo mysql_config_editor set --login-path=clubpromoters_test --host=localhost --user=clubpromoters_test --password
When prompted, paste the password and press Enter.



#### All environments
Go to the `FOLDER/clubpromoters-api` folder, activate the venv, and open up a flask shell:

    source venv/bin/activate
    flask shell
    
Create the admin account, all configuration files and exit the shell:

    create_admin("email", "password")
    create_config()
    exit()

Remember to deactivate the venv:

    deactivate

### Backups
The cronjobs scripts have been generated in the `FOLDER/clubpromoters-api/cron/` folder.

To set the automatic backups, open the cronab:

    crontab -e

Append the following to the file, and uncomment the backups that you wish to use:

    MAILTO=""
    
    
    # LIVE
    #0 * * * * ~/LIVE/clubpromoters-api/cron/hourly
    #@weekly ~/LIVE/clubpromoters-api/cron/weekly
    
    
    # TEST
    #@weekly ~/TEST/clubpromoters-api/cron/weekly
