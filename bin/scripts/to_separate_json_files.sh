input_file=$1
out_folder=$2

while read line
  do filename=$(sed -r 's/^.*"id": ?"([^"]*)\.(ece\d?|cms|json|html?|)".*$/\1.json/g' <(echo "$line"))
  echo "$line" > $out_folder/$filename
done<$input_file
