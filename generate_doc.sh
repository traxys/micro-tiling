#/bin/sh

make -C Millllllll/gopher html
mkdir -p docs/golfer
cp -r Millllllll/gopher/build/html/* docs/golfer


for service in API a_pi Millllllll client_library Unitator Translator
do
	make -C $service html
	mkdir -p docs/$service
	cp -r $service/build/html/* docs/$service
done
