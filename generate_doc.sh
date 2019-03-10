#/bin/sh

make -C Millllllll/gopher html
mkdir -p doc/golfer
cp -r Millllllll/gopher/build/html/* doc/golfer


for service in API a_pi Millllllll client_library Unitator Translator
do
	make -C $service html
	mkdir -p doc/$service
	cp -r $service/build/html/* doc/$service
done
