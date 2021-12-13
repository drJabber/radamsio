from radamsio import RadamsUrlIO


source = b'GET /auth?pass=HelloWorld HTTP1.1'
ri = RadamsUrlIO(source, mutations=16384)
print(ri.read())





