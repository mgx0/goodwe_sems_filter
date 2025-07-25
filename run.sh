docker build -t goodwe_sems_filter .
docker stop goodwe_sems_filter
docker rm goodwe_sems_filter
docker run -d \
  --name goodwe_sems_filter\
  --restart always \
  -e ENABLE_DOWNLOAD=False \
  -p 20001:20001 \
  goodwe_sems_filter
