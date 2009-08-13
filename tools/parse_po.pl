#!/usr/bn/perl

use Locale::Po4a::Po;

$po_directory = '/var/www/camptocamp.org/apps/frontend/i18n/';

$fr_po = $po_directory . 'messages.fr.po';
$it_po = $po_directory . 'messages.it.po';
$de_po = $po_directory . 'messages.de.po';
$en_po = $po_directory . 'messages.en.po';
$es_po = $po_directory . 'messages.es.po';
$ca_po = $po_directory . 'messages.ca.po';
$eu_po = $po_directory . 'messages.eu.po';

my $fr_pofile=Locale::Po4a::Po->new();
$fr_pofile->read($fr_po);
my $it_pofile=Locale::Po4a::Po->new();
$it_pofile->read($it_po);
my $de_pofile=Locale::Po4a::Po->new();
$de_pofile->read($de_po);
my $en_pofile=Locale::Po4a::Po->new();
$en_pofile->read($en_po);
my $es_pofile=Locale::Po4a::Po->new();
$es_pofile->read($es_po);
my $ca_pofile=Locale::Po4a::Po->new();
$ca_pofile->read($ca_po);
my $eu_pofile=Locale::Po4a::Po->new();
$eu_pofile->read($eu_po);

$count = $fr_pofile->count_entries();

for ($i = 0; $i < $count; $i++) {
  $msgid = $fr_pofile->msgid($i);

  print $msgid;
  print "\t";
  print $fr_pofile->gettext($msgid);
  print "\t";
  print $it_pofile->gettext($msgid);
  print "\t";
  print $de_pofile->gettext($msgid);
  print "\t";
  print $en_pofile->gettext($msgid);
  print "\t";
  print $es_pofile->gettext($msgid);
  print "\t";
  print $ca_pofile->gettext($msgid);
  print "\t";
  print $eu_pofile->gettext($msgid);
  print "\t";
  print "\n";

}
