#if 0
#include <SPI.h>
#include <PN532_SPI.h>
#include <PN532.h>
#include <NfcAdapter.h>

PN532_SPI pn532spi(SPI, 10);
NfcAdapter nfc = NfcAdapter(pn532spi);
#else

#include <Wire.h>
#include <PN532_I2C.h>
#include <PN532.h>
#include <NfcAdapter.h>

PN532_I2C pn532_i2c(Wire);
NfcAdapter nfc = NfcAdapter(pn532_i2c);
#endif

void setup(void) {
  Serial.begin(9600);
  Serial.setTimeout(5);
  Serial.println("NDEF Reader, Scan a NFC tag");
  nfc.begin();
}

void loop(void) {
  // 100 retries
  if (nfc.tagPresent(100))
  {
    Serial.println("Begin Tag");
    
    NfcTag tag = nfc.read();
    Serial.println(tag.getTagType());
    Serial.print("NFC Tag ID: ");Serial.println(tag.getUidString());

    if (tag.hasNdefMessage()) // every tag won't have a message
    {

      NdefMessage message = tag.getNdefMessage();
      Serial.print("This NFC Tag contains an NDEF Message with ");
      Serial.print(message.getRecordCount());
      Serial.print(" NDEF Record");
      if (message.getRecordCount() != 1) {
        Serial.print("s");
      }
      Serial.println(".");

      // cycle through the records, printing some info from each
      int recordCount = message.getRecordCount();
      for (int i = 0; i < recordCount; i++)
      {
        Serial.print("NDEF Record ");Serial.println(i+1);
        NdefRecord record = message.getRecord(i);
        // NdefRecord record = message[i]; // alternate syntax

        //Serial.print("  TNF: ");Serial.println(record.getTnf());
        //Serial.print("  Type: ");Serial.println(record.getType()); // will be "" for TNF_EMPTY

        // The TNF and Type should be used to determine how your application processes the payload
        // There's no generic processing for the payload, it's returned as a byte[]
        int payloadLength = record.getPayloadLength();
        byte payload[payloadLength];
        record.getPayload(payload);

        // Print the Hex and Printable Characters
        //Serial.print("  Payload (HEX): ");
        //PrintHexChar(payload, payloadLength);

        // Force the data into a String (might work depending on the content)
        // Real code should use smarter processing    
        if (record.getTnf() == TNF_WELL_KNOWN && record.getType() == "T") { // text message
          // skip the language code
          int startChar = payload[0] + 1;
          String payloadAsString = "";
          for (int c = startChar; c < payloadLength; c++) {
            payloadAsString += (char)payload[c];
          }
          //Serial.print("  Payload (as String): ");
          Serial.println(payloadAsString);
        } else {
          Serial.println("record on tag not of type Text, cannot show it");
        }

        // id is probably blank and will return ""
        String uid = record.getId();
        if (uid != "") {
          Serial.print("  ID: ");Serial.println(uid);
        }
      }
    }
    Serial.println("End Tag");
  }
  delay(1000);

}
