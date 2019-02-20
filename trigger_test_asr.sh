[ -f metadata/$1 ] && rm metadata/$1
filename_with_extension=$(basename -- "$1")
extension="${filename_with_extension##*.}"
filename="${filename_with_extension%.*}"
echo $filename
cp $1 metadata/"$filename"_"$(date "+%Y_%m_%d_%H_%M_%S").$extension"

