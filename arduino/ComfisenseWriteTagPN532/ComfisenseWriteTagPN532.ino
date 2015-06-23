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
      message.addTextRecord("ID;I001;ComfiSenseId");
      message.addTextRecord("Type;Long Sleeve shirt;Clothing type");
      message.addTextRecord("Id;0.33;Thermal insulation;clo");
      message.addTextRecord("Vres;0.0044;Moisture Vapor resistance;m**2 kPa/W");
      message.addTextRecord("Th;0.8;Thickness;mm");
      message.addTextRecord("W;100.0;Weigth;g");
      message.addTextRecord("C;#FF0000;Color;hex");
    
        boolean success = nfc.write(message);
        if (success) {
            Serial.println("Success. Try reading this tag with your phone.");
        } else {
            Serial.println("Write failed");
        }
    }
    delay(3000);
}
