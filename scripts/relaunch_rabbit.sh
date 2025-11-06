ulimit -S -n 32000
while [ 0 -lt 1 ]
do
	cd old_pymp
	/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/rabbitMQ/start_rabbitmq_roshea.sh
	sleep 60
done
	

