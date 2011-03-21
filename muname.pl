#!/usr/bin/perl

use warnings;
use strict;

use File::Temp qw/tempdir/;
use File::Find;
use Cwd qw/abs_path getcwd/;
use Getopt::Long;

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
	return s/^([tT]he) (.*)$/$2, $1/;
}


if ($ACT) {
	mkdir($OUTPUT);
	chdir($OUTPUT);
} else {
	print "No changes will be made\n\n";

	my $dir = &tempdir( CLEANUP => 1 );
	chdir($dir);
}

sub wanted() {
	if ($_ !~ /\.mp3$/) {
		return 0;
	}

	if (! -r $File::Find::name) {
		return;
	}

	my $file = $File::Find::name;

	print $file . "\n";
}

# find all mp3 files in the folders
&find(\&wanted, @folders);


chdir($curdir);
