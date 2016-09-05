ARCTIC PROJECT

          _/\
         /   \  
         |    \
       _/      |
      /         \
_____/           \________


docker build:
docker build -t arctic .

docker run command:
docker run -d -p 80:80 --net=host --name arctic -v /root/arctic/docs:/docs arctic

