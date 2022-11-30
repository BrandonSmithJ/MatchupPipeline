#!/bin/bash


# Hardcoded path to RabbitMQ files which everyone needs access to
SHARED="/discover/nobackup/bsmith16/Matchups_Files"

# RabbitMQ installation
RMQ_DIR=$(ls rabbitmq_server-*)

# Location to store RabbitMQ server outputs
RMQ_LOG="$SHARED/RabbitMQ.log"

# File containing the hostname where the RabbitMQ server is currently running
RMQ_HOST="$SHARED/RMQ_host"

# Directory containing TLS certificates
TLS_DIR="$SHARED/TLS"

# Name of the screen which rabbitmq will run in
SCREEN_NAME="rabbitmq"

# Command to check if RabbitMQ is running (using the hostname if it exists)
RUN_CHECK="$RMQ_DIR/sbin/rabbitmqctl status --node rabbit$(cat $RMQ_HOST 2>/dev/null) >/dev/null 2>&1"

# Command to start the server
START_RMQ="$RMQ_DIR/sbin/rabbitmq-server > $RMQ_LOG 2>&1"

# Add in the addition of logging the hostname when starting/stopping 
START_RMQ="echo '@$(hostname)' > $RMQ_HOST; $START_RMQ; rm $RMQ_HOST"

# RabbitMQ configuration settings
RMQ_CONFIG=$(cat <<-EOF
# RabbitMQ configuration file
#   Should be placed in rabbitmq/etc/rabbitmq/rabbitmq.conf

# Server admins require cleartext messages to be disabled
listeners.tcp = none
listeners.ssl.default = 5671

# Should technically be absolute paths
ssl_options.cacertfile = $TLS_DIR/ca-cert.pem
ssl_options.certfile = $TLS_DIR/server-cert.pem
ssl_options.keyfile = $TLS_DIR/server-key.pem
ssl_options.verify = verify_peer
ssl_options.fail_if_no_peer_cert = true

# Allow only TLSv1.2
ssl_options.versions.1 = tlsv1.2

# Allow only TLSv1.3 - not yet available
#ssl_options.versions.1 = tlsv1.3
#ssl_options.ciphers.1 = TLS_AES_256_GCM_SHA384
#ssl_options.ciphers.2 = TLS_AES_128_GCM_SHA256
#ssl_options.ciphers.3 = TLS_CHACHA20_POLY1305
#ssl_options.ciphers.4 = TLS_AES_128_CCM_SHA256
#ssl_options.ciphers.5 = TLS_AES_128_CCM_8_SHA256

# Some jobs need longer than 15 minutes to ack
consumer_timeout = 31622400000
EOF
)

# ----------------------------------------


# Ensure the screen directory is properly set; screens need to be
#   stored in the home directory so that they aren't unique to each
#   discover node
warning="Set your SCREENDIR env var so screens are universal across nodes"
suggest="(e.g. echo 'export SCREENDIR=~/.screens' >> ~/.bashrc && source ~/.bashrc)"
[ ! -z "$SCREENDIR" ] || { echo "$warning $suggest"; exit 1; }

# Check that the rabbitmq folder is available
[ -d $RMQ_DIR ] || { echo "$RMQ_DIR does not exist"; exit 1; }

# Check if RabbitMQ is already running
eval "$RUN_CHECK" && { echo "RabbitMQ is already running $(cat $RMQ_HOST 2>/dev/null)"; exit 0; }

# Check if TLS certificates exist, and if not, create them
if [ ! -d $TLS_DIR ]; then

    # Write the configuration file
    echo "$RMQ_CONFIG" > $RMQ_DIR/etc/rabbitmq/rabbitmq.conf

    # Copy helper scripts
    echo "Generating TLS certificates in $TLS_DIR..."
    mkdir -p $TLS_DIR
    chmod 755 $TLS_DIR
    cd $TLS_DIR

    # Create TLS certificates
    openssl req -x509 -newkey rsa:4096 -days 36500 -nodes -keyout ca-key.pem -out ca-cert.pem -subj "/C=US/ST=MD/CN=localhost"
    openssl req -newkey rsa:4096 -nodes -keyout server-key.pem -out server-req.pem -subj "/C=US/ST=MD/CN=server"
    openssl x509 -req -in server-req.pem -days 36500 -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem
    openssl verify -CAfile ca-cert.pem server-cert.pem
    chmod 755 *.pem

    cd -
fi

# Create screen and run RabbitMQ
echo -n "Starting RabbitMQ..."
screen -dmS $SCREEN_NAME bash -c "$START_RMQ; echo 'RabbitMQ exited.'; sleep 40;"
sleep 10

# Check that RabbitMQ started successfully
eval "$RUN_CHECK" || { echo "failed."; exit 1; }
echo "success!"

# Ensure log file is accessible to everyone
touch $RMQ_LOG
chmod 755 $RMQ_LOG

