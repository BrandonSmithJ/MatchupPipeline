#!/bin/bash

user=$1
rabbitmqctl add_user $user mp$user
rabbitmqctl set_user_tags $user administrator
rabbitmqctl delete_vhost matchups_$user
rabbitmqctl add_vhost matchups_$user
rabbitmqctl set_permissions -p matchups_$user $user ".*" ".*" ".*"
