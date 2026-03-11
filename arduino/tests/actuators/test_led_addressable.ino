#include <Adafruit_NeoPixel.h>

// 연결 정보 설정
#define LED_PIN     5   // 아두이노 우노 R4 WiFi의 D5 핀 (데이터 라인과 핀 사이에 250옴 저항 연결됨)
#define TOTAL_LEDS  100 // 100개 직렬 연결
#define USE_LEDS    20  // 그 중 사용할 20개

Adafruit_NeoPixel strip(TOTAL_LEDS, LED_PIN, NEO_RGB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);   // 시리얼 통신 시작 (보드레이트 115200)
  
  strip.begin();           // LED 객체 초기화
  strip.clear();           // 초기에 100개 전체 끄기 상태
  strip.show();            // 꺼진 상태 적용
  strip.setBrightness(50); // 사용할 LED 밝기 (0~255)
  
  Serial.println("=========================================");
  Serial.println("WS2811 수동 제어 모드 (D5 핀)");
  Serial.println("시리얼 모니터에 R,G,B 값을 쉼표로 구분하여 입력하세요.");
  Serial.println("이제 입력 후 다음 명령을 줄 때까지 색상이 계속 켜져 있습니다!");
  Serial.println("예시:");
  Serial.println(" '255,0,0'   : 빨강색으로 켜기");
  Serial.println(" '0,255,0'   : 초록색으로 켜기");
  Serial.println(" '255,255,0' : 노랑색으로 켜기");
  Serial.println(" '0,0,0'     : 완전히 끄기");
  Serial.println("=========================================");
  Serial.println("입력을 기다리는 중...");
}

void loop() {
  // 시리얼 입력이 올 때까지 대기
  if (Serial.available() > 0) {
    // 줄바꿈 문자(\n)가 도달할 때까지 한 줄을 통째로 읽어옵니다.
    String input = Serial.readStringUntil('\n');
    input.trim(); // 눈에 보이지 않는 공백, 캐리지리턴(\r) 등을 제거하여 쓰레기값 방지
    
    // 비어있는 입력(단순 엔터 입력 등)은 무시
    if (input.length() > 0) {
      
      // 쉼표 두 개가 있는지 확인して 문자열 분리
      int firstComma = input.indexOf(',');
      int secondComma = input.indexOf(',', firstComma + 1);
      
      if (firstComma > 0 && secondComma > firstComma) {
        int r = input.substring(0, firstComma).toInt();
        int g = input.substring(firstComma + 1, secondComma).toInt();
        int b = input.substring(secondComma + 1).toInt();
        
        // 입력받은 값을 0~255 안전 범위로 제한
        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);
        
        Serial.print("=> 수신된 RGB 적용: (");
        Serial.print(r);
        Serial.print(", ");
        Serial.print(g);
        Serial.print(", ");
        Serial.print(b);
        Serial.println(") - 상태 유지 중");

        // 설정한 색상으로 LED 켜기
        setColor(r, g, b);
      } else {
        Serial.println("입력 형식이 잘못되었습니다. '255,0,0' 처럼 쉼표로 세 개의 숫자를 입력해주세요.");
      }
    }
  }
}

// 스트립 내 사용할 개수(USE_LEDS)만큼 색상 변경 후 반영하는 함수
void setColor(uint8_t red, uint8_t green, uint8_t blue) {
  strip.clear(); // 전체를 먼저 지워 잔상 방지
  
  // 0번부터 지정된 USE_LEDS 개의 LED에만 색상을 입힙니다.
  for(int i = 0; i < USE_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(red, green, blue));
  }
  strip.show(); // 설정한 색상값을 실제 하드웨어에 전송하여 업데이트
}
