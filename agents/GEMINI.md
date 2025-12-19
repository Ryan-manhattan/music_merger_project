# Claude Instructions for Music Merger Project

This file contains instructions and context for Claude when working on the music merger project.

## Project Overview
A music merger application that combines and processes audio files.

## Development Commands
- `npm run dev` - Start development server
- `npm run build` - Build the project
- `npm run test` - Run tests
- `npm run lint` - Run linting
- `npm run typecheck` - Run TypeScript type checking

## Code Style Guidelines
- Follow existing code conventions in the project
- Use TypeScript for type safety
- Follow consistent naming conventions
- Add comments only when explicitly requested

## Testing
- Run tests before committing changes
- Ensure all type checks pass
- Run linting to maintain code quality

## Important Notes
- Always check existing dependencies before adding new ones
- Follow security best practices
- Never commit secrets or API keys
- Use existing patterns and libraries when possible

---

# [기본 작업 운영 지침서] 가장 중요

1. 절대 나의 동의 없이 임의로 진행하지말 것
2. 옵션 제시는 숫자로 할 것 추천 옵션도 함께 제시할 것
3. 오류 발생 시 원인 분석 후 해결 방법을 제시할 것
4. 모든 수정 및 진행 과정은 나에게 허락을 구하고 진행할 것
5. 모든 대답과 의견은 토큰을 가장 효율적으로 사용할 수 있는 방법으로 제시
6. 언제나 한글로 대답한다
5. md 문서의 기존 내용은 절대로 삭제하지 않고, 새로운 내용을 추가한다.(효율성 중심)
6. 새롭게 알게 된 사실이나 다시 참고해야하는 팁은 매번 룰로 생성한다 

## [작업 전/중/후 필수 규칙]

## 🚦 [진행 및 의사결정]

1. 모든 작업은 사용자에게 반드시 확인 후 수행
2. 이후 진행 여부 질문은 숫자 옵션과 추천 항목을 간단히 제시
2. 지시어 예시:
   - `ㄱ` = 진행
   - `ㅇㅇ` = 알겠어
   - `ㄱㄱㄱ` = 질문 없이 전체 자동 진행
   - `ㅁㅁㄹ` = memory.md 업데이트
   - `ㄹㄷㅁ` = READEME.md 업데이트
   - 'ㅌㄷ' = To-Do.md 업데이트 
   - 'ㅇㄹ' = error.md 업데이트
   - 'ㅂㄱ' = 작업 진행 하지말고 보고만 진행
   - 'ㄽㅅ' = 커서 프로젝트 룰 생성

## 🧠 [의견 및 옵션 제공 규칙]

1. 질문에 대한 답변만 제시하고 정답만 제시 할 것
2. 오류 발생 시:
   - 원인 분석 후 바로 조치 하지 말 것
   - 사용자에게 원인 및 해결 옵션 제시 할 것
   - 해결되면 반드시 룰로 생성

## 📂 [파일/폴더 관리 지침]

1. 생성 및 수정은 해당 프로젝트 폴더 내에서만 수행
2. 파일 용량 및 구조 최적화:
   - 한 파일은 **18KB 초과 금지**
   - 긴 파일은 **2~3개 단위 분할**
3. `docs/` 폴더에는 꼭 필요한 문서만 최소 용량으로 정리

## 🧪 [테스트/디버깅/코딩]

1. 테스트는 **MCP 도구(예: Playwright)** 사용
   - 브라우저 상에서 직접 클릭 → 결과 확인
3. 디버깅 시 **콘솔 로그 필수 확인**
4. 에러 발생시 디버깅 가능한 코드 추가