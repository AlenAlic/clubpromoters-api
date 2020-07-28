# clubpromoters-api installation (Ubuntu 18.04 LTS)
Installation guide for the clubpromoters-api

## Preparation


### Installer instance
We'll use an instance of clubpromoters-api to install everything else.

    git clone https://github.com/AlenAlic/clubpromoters-api
    cd clubpromoters-api
    
### Base items
To install all the base dependencies, run the `install_base` script.

    source scripts/install_base
    
From here you can run any of the installations located in the scripts folder.


### Mail
If you do not have any active mail credentials, it is advised you install the mailserver repository first, found at: [https://github.com/AlenAlic/mailserver](https://github.com/AlenAlic/mailserver) 

This will configure the server to be able to send and receive mail, something that the clubpromoters-api needs. 


## Different instances

### test
Before installing the demo instance, set the following environment variables:

    export TEST_EMAIL_ADDRESS=
    export TEST_EMAIL_PASSWORD=
Then run the installation script:

    source scripts/install_test
Finally, copy the `TEST_DB_PASSWORD` and run the following command to create a login path for cronjobs to run backups:

    sudo mysql_config_editor set --login-path=$TEST_FOLDER --host=localhost --user=$TEST_DB_USERNAME --password
When prompted, paste the password and press Enter.

To update the api, just run

    test-api-update

### demo
Before installing the demo instance, set the following environment variables:

    export DEMO_EMAIL_ADDRESS=
    export DEMO_EMAIL_PASSWORD=
Then run the installation script:

    source scripts/install_demo
Finally, copy the `DEMO_DB_PASSWORD` and run the following command to create a login path for cronjobs to run backups:

    sudo mysql_config_editor set --login-path=$DEMO_FOLDER --host=localhost --user=$DEMO_DB_USERNAME --password
When prompted, paste the password and press Enter.

To update the api, just run

    demo-api-update


## Add admin and set configuration
Navigate to the root folder of whatever instance you wish add the user to, and run
    
    source venv/bin/activate

    flask admin add -email email@example.com -p password -fn first_name -ln last_name
    
    flask admin config
    
    deactivate
