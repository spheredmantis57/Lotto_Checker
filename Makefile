mkfile_path := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
build_path := $(mkfile_path)build
exe_name := lottery
lottery_exe_path := /app/dist/$(exe_name)

i := 0
print_stage_number = @echo "CALLING STAGE $(i): $(1)..." $(eval i=$(shell echo $$(($(i)+1))))
all: clean linux_compile

.PHONY: set_up
set_up:
	$(call print_stage_number, "set up")
	@mkdir -p $(build_path)
		
.PHONY: linux_compile
linux_compile: set_up linux_docker_pull
	$(call print_stage_number, "linux compile")
	@sudo docker build . --pull --quiet --force-rm --network="host" -t linux_img >/dev/null
	@sudo docker run --entrypoint /bin/sh linux_img -c "cat $(lottery_exe_path)" > $(build_path)/linux_$(exe_name).exe
	@chmod +x $(build_path)/linux_$(exe_name).exe
	@sudo docker rmi linux_img -f > /dev/null
	
.PHONY: clean
clean:
	$(call print_stage_number, "clean")
	@rm -f $(build_path)/*
	
# check if docker imgaes exist
image_exists := $(shell sudo docker images | grep mono | wc -l)
linux_docker_pull:
ifeq ($(image_exists), 0)
	$(call print_stage_number, "pulling linux docker")
	@sudo docker pull mono
endif
