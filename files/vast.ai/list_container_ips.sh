#!/bin/bash
COUNT=0
for container in $(docker ps -q); do
    COUNT=$((COUNT + 1))
done

echo "{"
COUNTER=1
for container in $(docker ps -q); do
    ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $container)
    name=$(docker inspect -f '{{.Name}}' $container)
    if [[ $COUNTER -lt $COUNT ]]
    then
        echo '"'"$name"'"': '"'"$ip"'",';
    else
        echo '"'"$name"'"': '"'"$ip"'"';
    fi
    COUNTER=$((COUNTER + 1))
done
echo "}"
