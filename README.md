# faceplusplus-sdk-py3
a simple facepp sdk for python3



Face++官方提供的sdk所使用的python环境为python2.x，
此代码将原sdk中的python2.x特有的包替换为python3.x
能够使用的包，以适应python3.x环境。


    API_KEY = "您的API_KEY"
    API_SECRET = "您的API_SECRET"

    api = API(key=API_KEY, secret=API_SECRET)
    ret = api.detect(image_file=File('../timg.jpeg'), return_landmark=0, return_attributes='none')
    print('*****' * 6)
    print(ret)
    ret = api.compare(image_file1=File('../timg.jpeg'), image_file2=File('../timg.jpeg'))
    print('*****' * 6)
    print(ret)
    ret = api.search(image_file=File('../timg.jpeg'), faceset_token="151")
    print('*****' * 6)
    print(ret)
