from gpiozero import OutputDevice
import time

# 릴레이가 연결된 GPIO 핀 번호 (BCM 모드 기준)
RELAY_PIN = 26

def main():
    # gpiozero의 OutputDevice를 사용하여 릴레이 제어
    # initial_value=False로 설정하여 시작 시 릴레이를 끈 상태로 유지합니다.
    # 만약 신호가 반대로 동작(Low-Active)한다면 active_high=False로 변경하세요.
    relay = OutputDevice(RELAY_PIN, active_high=False, initial_value=True)
    
    print("====================================")
    print(f"릴레이 제어 테스트 (GPIO {RELAY_PIN}번 핀)")
    print("명령어:")
    print("  '1' 또는 'on'  : 릴레이 켜기")
    print("  '0' 또는 'off' : 릴레이 끄기")
    print("  'q' 또는 'quit': 프로그램 종료")
    print("====================================")
    
    try:
        while True:
            cmd = input("\n명령을 입력하세요: ").strip().lower()
            
            if cmd in ['1', 'on']:
                relay.on()
                print(">>> 릴레이 상태: ON 신호 전송")
            elif cmd in ['0', 'off']:
                relay.off()
                print(">>> 릴레이 상태: OFF 신호 전송")
            elif cmd in ['q', 'quit', 'exit']:
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 명령입니다. '1', '0', 'on', 'off', 'q' 중 하나를 입력하세요.")
                
    except KeyboardInterrupt:
        print("\n키보드 입력(Ctrl+C)으로 인해 프로그램을 종료합니다.")
    finally:
        # gpiozero는 스크립트 종료 시 핀을 자동으로 해제하지만, 
        # 안전을 위해 명시적으로 끄고 자원을 반환합니다.
        relay.off()
        relay.close()
        print("GPIO 리소스를 안전하게 해제했습니다.")

if __name__ == '__main__':
    main()
