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

void setup() {
    Serial.begin(9600);
    Serial.println("NDEF Writer");
    nfc.begin();
}

void loop() {
    Serial.println("\nPlace a formatted Mifare Classic NFC tag on the reader.");
    if (nfc.tagPresent()) {
      NdefMessage message = NdefMessage();
      message.addTextRecord("ID;I001;;Type;Short Sleeve shirt;;Id;0.33;m**2 kPa/W");
      //message.addTextRecord("Type;Long Sleeve shirt");   //Clothing type
      //message.addTextRecord("Id;0.33;clo");              //Thermal insulation;
      message.addTextRecord("Vres;0.00522;m**2 kPa/W;;Th;0.8;mm;;W;100.0;g;;C;#00008B;hex");   //Moisture Vapor resistance;
      //message.addTextRecord("Th;0.8;;mm");               //Thickness
      //message.addTextRecord("W;100.0;g");                //Weigth
      //message.addTextRecord("C;#FF0000;hex");            //Color
      message.addTextRecord("URL;cage.ugent.be/~bm/pics/comfisense/shirt_case1.jpg");

      boolean success = nfc.write(message);
      if (success) {
          Serial.println("Success. Try reading this tag with your phone.");
      } else {
          Serial.println("Write failed");
      }
    }
    delay(3000);
}
