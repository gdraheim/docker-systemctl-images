#! /bin/bash

if [ -n "{{postgres_enable}}" ]; then
  source {{postgres_enable}}
fi

postgres_host="{{postgres_host}}"
postgres_port="{{postgres_port}}"

for i in 1 2 3 4 5 6 7 8 9; do
  pg_isready -h $postgres_host -p $postgres_port && exit 0
  sleep 1
done

exit 1
