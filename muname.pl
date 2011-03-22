#!/usr/bin/perl

use warnings;
use strict;

use Cwd qw/abs_path getcwd/;
use Data::Dumper;
use File::Basename;
use File::Copy;
use File::Find;
use File::Path qw/mkpath/;
use File::Temp qw/tempdir/;
use File::Spec;
use Getopt::Long;

use MP3::Info;

my $ACT = 0;
my $OUTPUT = "./sorted";
my $curdir = &getcwd;

GetOptions("act" => \$ACT, "destination=s" => \$OUTPUT);

my @folders = map { &abs_path($_) } grep { -d $_ } @ARGV;

if ($#folders != $#ARGV) {
	print "Bad path given\n";
	exit(1);
}

sub normalize() {
	my $name = pop;
	$name =~ s/^([tT]he) (.*)$/$2, $1/;
	$name =~ s/\//\\\//;
	return $name;
}

sub fakerename() {
	my ($from, $to) = @_;

	my $dir = &dirname($to);
	&mkpath($dir);

	open(TEMP, ">", "$to");
	close(TEMP);
}

sub realrename() {
	my ($from, $to) = @_;

	my $dir = &dirname($to);
	&mkpath($dir);

	# mv the file
	rename $from, $to;
}

my $renamer = $ACT ? \&realrename : \&fakerename;

sub wanted() {
	if ($_ !~ /\.mp3$/) {
		return;
	}

	if (! -r $File::Find::name) {
		return;
	}

	my $file = $File::Find::name;
	my $tag = get_mp3tag($file);

	# make sure file has all the stuff
	my @attrs = qw/ARTIST TITLE TRACKNUM ALBUM/;

	foreach (@attrs) {
		my $str = $tag->{$_} || "";
		chomp($str);
		if (!$str) {
			print "File has bad id3 data: $file\n";
			print "$_ -> " . $tag->{$_} . "\n";
			return;
		}
	}

	if ($tag->{TRACKNUM} !~ /^\d+(?:\/\d+)?$/) {
		print "Track num looks weird ($file)\n";
		return;
	}


	(my $track = $tag->{TRACKNUM} )=~ s/\/\d+$//;
	$track = sprintf("%0.2d", $track);

	my $artist = &normalize($tag->{ARTIST});
	my $album = &normalize($tag->{ALBUM});
	my $title = &normalize($tag->{TITLE});


	# now deal with the file
	my $dest = File::Spec->catfile($OUTPUT, $artist, $album, "$track - $title.mp3");

	&$renamer($file, $dest);
}

$OUTPUT = &abs_path($OUTPUT);

if ($ACT) {
	mkdir($OUTPUT);
} else {
	print "No changes will be made\n\n";

	my $dir = &tempdir( CLEANUP => 1 );
	$OUTPUT = $dir;
}

# find all mp3 files in the folders
&find(\&wanted, @folders);

# print out all the stuff
print `cd "$OUTPUT" && ls -R`;

chdir($curdir);
