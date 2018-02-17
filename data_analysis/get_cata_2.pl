#!/usr/bin/perl

my %h = ();

while(<>) {
	$_ =~ s/.*categories"//;
	my @F = ($_ =~ m/"(.+?)"(?:,|\])/g );
	for my $a (@F) {
		$h{$a} ++;
	}
}

for my $k (sort { $h{$b} <=> $h{$a} } keys %h) {
	print "$k:\t$h{$k}\n";
}

