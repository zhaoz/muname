#!/bin/bash -e

NO_ACT=0

while getopts ":n" o; do
	case "$o" in
		n)
			NO_ACT=1 ;;
	esac
done

shift $(($OPTIND - 1))

if [ -z "$1" ]; then
	FOLDER="."
else
	FOLDER=$1
fi

shift

if [ -z "$1" ]; then
	SORTED="sorted"
else
	SORTED=$1
fi

mkdir -p "$SORTED"

# are there any non music files in here

if [ ! -d "$FOLDER" ]; then
	echo "Given folder is bogus"
	exit 1
fi

FOLDER=`readlink -f "$FOLDER"`

echo "acting on folder: $FOLDER"
echo

function fake_rename () {
	DEST=$2
	touch "$DEST"
}

RENAME="mv"

if [ $NO_ACT -eq 1 ]; then
	echo "Will not make any changes"

	# make a temp dir
	TMPDIR=`mktemp -d`
	cd "$TMPDIR"

	RENAME="fake_rename"
else
	cd "$SORTED"
fi

function normalize() {
	echo "$1" | sed 's/^\([tT]he\) \(.*\)$/\2, \1/'
}


# act on all MP3s
for path in "${FOLDER}"/*.mp3; do
	name=`basename "$path"`

	title=""
	artist=""
	album=""
	track=""

	# get some info on the song
	cnt=0

	ORIGIFS=$IFS
	IFS=`echo -en "\n\b"`
	for xx in `mp3info "${path}" -p "%a\n%l\n%t\n%0.2n"`; do
		xx=`normalize "$xx"`
		case $cnt in 
			0) artist="$xx" ;;
			1) album="$xx" ;;
			2) title="$xx" ;;
			3) track="$xx" ;;
		esac
		cnt=$(( $cnt + 1 ))
	done
	IFS=$ORIGIFS

	if [ -z "$artist" -o -z "$album" -o -z "$title" -o -z "$track" ]; then
		echo "File does not have good id3 data!"
		echo "    $path"
		echo ""
		echo "exiting"
		exit 1
	fi

	dest="${artist}/${album}/${track} - ${title}.mp3"

	fpath=`dirname "$dest"`

	mkdir -p "${fpath}"

	$RENAME "$path" "$dest"
done

if [ -d "$TMPDIR" ]; then
	ls -R
	rm -rf "$TMPDIR"
fi
