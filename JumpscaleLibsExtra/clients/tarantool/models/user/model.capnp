@0xbc08a7d76708ae85;

#is example code, not to be used anywhere

struct User {
  region @0   :UInt16; #is identificaton of region, in beginning = 0
  id @1       :UInt32; #4 bytes, means max 4billion entries max
  epoch @2    :UInt32; #moddate
  pubkey @3   :Data; #32 bytes (use https://github.com/philanc/luatweetnacl)
  history @4  :UInt32; #if there is a previous version of this user (e.g. if pubkey changes)
  sign @5     :Data; #48 bytes: has been signed by secret key of User & returns the 16 byte blake hash of previousobj:sign + current:region+rid+epoch+pubkey+history+link
  link @6     :UInt32; #link to Base object which has all data for this user in namespace 1 which is special namespace for user
  name @7     :Text;
  description @8     :Text;
  guid @9     :Text;
}
