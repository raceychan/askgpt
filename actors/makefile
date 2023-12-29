OUT_DIR=./src/proto

generate:
	python -m grpc_tools.protoc \
	--proto_path=../proto \
	--python_out=$(OUT_DIR) \
	--grpc_python_out=$(OUT_DIR) \
	--pyi_out=$(OUT_DIR) \
	../proto/$(file)	

#../proto/*.proto

