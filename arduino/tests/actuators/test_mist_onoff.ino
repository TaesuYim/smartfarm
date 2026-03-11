#define MIST_PIN 8 // 아두이노 D8 핀 (MOSFET Gate 연결)

void setup() {
  Serial.begin(115200);   // 시리얼 통신 시작 (보드레이트 115200)
  
  pinMode(MIST_PIN, OUTPUT);
  digitalWrite(MIST_PIN, LOW); // 초기 상태는 미스트 꺼짐(OFF) 상태로 설정
  
  Serial.println("=====================================");
  Serial.println("초음파 미스트 제어 테스트 (D8 핀/MOSFET)");
  Serial.println("시리얼 모니터에 아래 명령어를 입력해보세요:");
  Serial.println(" '1' : 미스트 켜기 (ON)");
  Serial.println(" '0' : 미스트 끄기 (OFF)");
  Serial.println("=====================================");
}

void loop() {
  // 시리얼 모니터에서 입력값이 있는지 확인
  if (Serial.available() > 0) {
    char cmd = Serial.read(); // 입력된 첫 번째 문자 읽기
    
    // 불필요한 줄바꿈(\n), 캐리지리턴(\r), 공백 문자 등은 무시
    if (cmd == '\n' || cmd == '\r' || cmd == ' ') return;
    
    // 명령어에 따라 다르게 처리
    if (cmd == '1') {
      digitalWrite(MIST_PIN, HIGH); // MOSFET의 Gate에 HIGH(5V 내지 3.3V)를 인가하여 미스트 On
      Serial.println("=> 명령어 수신: '1' -> 초음파 미스트 켜짐 (ON)");
    } 
    else if (cmd == '0') {
      digitalWrite(MIST_PIN, LOW);  // MOSFET의 Gate에 LOW를 인가하여 미스트 Off
      Serial.println("=> 명령어 수신: '0' -> 초음파 미스트 꺼짐 (OFF)");
    } 
    else {
      // 지정되지 않은 명령어가 들어온 경우
      Serial.print("알 수 없는 명령어입니다: ");
      Serial.println(cmd);
    }
  }
}
