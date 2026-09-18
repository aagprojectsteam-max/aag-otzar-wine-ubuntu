/* Owned Wine-prefix keyboard repair. Never stores text or changes focus. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define TAG ((ULONG_PTR)0x41414753)
typedef struct {WORD vk,scan;DWORD flags;unsigned group;} Key;
static const Key keys[]={
 {VK_LWIN,0x5b,KEYEVENTF_EXTENDEDKEY,1},{VK_RWIN,0x5c,KEYEVENTF_EXTENDEDKEY,1},
 {VK_LMENU,0x38,0,2},{VK_RMENU,0x38,KEYEVENTF_EXTENDEDKEY,2},{VK_MENU,0x38,0,2},
 {VK_LCONTROL,0x1d,0,4},{VK_RCONTROL,0x1d,KEYEVENTF_EXTENDEDKEY,4},{VK_CONTROL,0x1d,0,4},
 {VK_LSHIFT,0x2a,0,8},{VK_RSHIFT,0x36,0,8},{VK_SHIFT,0x2a,0,8}};
static HHOOK hook;static HANDLE response;static CRITICAL_SECTION cs;
static DWORD main_tid,sequence,answer_id;static unsigned answer_mask;
static volatile LONG closing;static BOOL repairing;
static unsigned mask(void){unsigned m=0;for(unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)if(GetAsyncKeyState(keys[i].vk)&0x8000)m|=keys[i].group;return m;}
static BOOL modifier(DWORD vk){for(unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)if(keys[i].vk==vk)return TRUE;return FALSE;}
static BOOL target(HWND *window,GUITHREADINFO *gui){
 wchar_t title[128]={0};*window=GetForegroundWindow();GetWindowTextW(*window,title,127);
 if(!*window||!IsWindowVisible(*window)||lstrcmpiW(title,L"otzar"))return FALSE;
 memset(gui,0,sizeof(*gui));gui->cbSize=sizeof(*gui);
 return GetGUIThreadInfo(GetWindowThreadProcessId(*window,NULL),gui);
}
static DWORD WINAPI reader(LPVOID ignored){
 char line[80];(void)ignored;
 while(fgets(line,sizeof(line),stdin)){unsigned long id;unsigned m;char tail;
  if(sscanf(line,"%lu %u %c",&id,&m,&tail)!=2||m>15)continue;
  EnterCriticalSection(&cs);answer_id=(DWORD)id;answer_mask=m;LeaveCriticalSection(&cs);SetEvent(response);
 }
 InterlockedExchange(&closing,1);SetEvent(response);PostThreadMessageW(main_tid,WM_QUIT,0,0);return 0;
}
static unsigned physical_certificate(unsigned stale){
 DWORD id=++sequence;ULONGLONG start=GetTickCount64();ResetEvent(response);
 printf("{\"kind\":\"CHECK\",\"id\":%lu,\"stale\":%u}\n",(unsigned long)id,stale);fflush(stdout);
 while(!closing&&GetTickCount64()-start<90){
  DWORD left=(DWORD)(90-(GetTickCount64()-start));if(left>90)break;
  if(WaitForSingleObject(response,left)!=WAIT_OBJECT_0)break;
  EnterCriticalSection(&cs);DWORD got=answer_id;unsigned allowed=answer_mask;LeaveCriticalSection(&cs);
  if(got==id)return allowed;
 }
 puts("{\"kind\":\"CERTIFICATE_TIMEOUT\"}");fflush(stdout);return 0;
}
static BOOL repair(const KBDLLHOOKSTRUCT *original){
 HWND window;GUITHREADINFO before,after;unsigned stale=mask();
 if(!stale||!target(&window,&before))return FALSE;
 unsigned allowed=physical_certificate(stale);unsigned selected=mask()&allowed;
 if(!selected||GetForegroundWindow()!=window)return FALSE;
 INPUT batch[12];memset(batch,0,sizeof(batch));UINT count=0;
 for(unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)if(selected&keys[i].group){
  batch[count].type=INPUT_KEYBOARD;batch[count].ki.wVk=keys[i].vk;batch[count].ki.wScan=keys[i].scan;
  batch[count].ki.dwFlags=KEYEVENTF_KEYUP|keys[i].flags;batch[count].ki.dwExtraInfo=TAG;count++;
 }
 if(original){
  batch[count].type=INPUT_KEYBOARD;batch[count].ki.wVk=(WORD)original->vkCode;
  batch[count].ki.wScan=(WORD)original->scanCode;
  batch[count].ki.dwFlags=(original->flags&LLKHF_EXTENDED)?KEYEVENTF_EXTENDEDKEY:0;
  batch[count].ki.dwExtraInfo=TAG;count++;
 }
 repairing=TRUE;UINT sent=SendInput(count,batch,sizeof(INPUT));repairing=FALSE;
 memset(&after,0,sizeof(after));after.cbSize=sizeof(after);GetGUIThreadInfo(GetWindowThreadProcessId(window,NULL),&after);
 printf("{\"kind\":\"REPAIR\",\"selected\":%u,\"requested\":%u,\"sent\":%u,\"replayed\":%s,\"backspace\":%s,\"focus_unchanged\":%s}\n",selected,count,sent,original?"true":"false",original&&original->vkCode==VK_BACK?"true":"false",GetForegroundWindow()==window&&before.hwndFocus==after.hwndFocus?"true":"false");fflush(stdout);
 return original&&sent==count;
}
static LRESULT CALLBACK keyboard(int code,WPARAM message,LPARAM param){
 if(code==HC_ACTION&&!repairing&&(message==WM_KEYDOWN||message==WM_SYSKEYDOWN)){
  const KBDLLHOOKSTRUCT *event=(const KBDLLHOOKSTRUCT*)param;
  if(event->dwExtraInfo!=TAG&&!modifier(event->vkCode)&&event->vkCode!=VK_PACKET&&event->vkCode!=VK_PROCESSKEY)
   if(repair(event))return 1;
 }
 return CallNextHookEx(hook,code,message,param);
}
int main(int argc,char **argv){
 BOOL timer_enabled=TRUE;
 if(argc==2&&!strcmp(argv[1],"--no-timer"))timer_enabled=FALSE;
 else if(argc!=1)return 2;
 main_tid=GetCurrentThreadId();MSG msg;PeekMessageW(&msg,NULL,0,0,PM_NOREMOVE);
 InitializeCriticalSection(&cs);response=CreateEventW(NULL,FALSE,FALSE,NULL);
 if(!response)return 3;
 HANDLE thread=CreateThread(NULL,0,reader,NULL,0,NULL);if(!thread)return 4;
 hook=SetWindowsHookExW(WH_KEYBOARD_LL,keyboard,GetModuleHandleW(NULL),0);
 if(!hook){printf("{\"kind\":\"HOOK_FAILED\",\"error\":%lu}\n",GetLastError());return 5;}
 UINT_PTR timer=timer_enabled?SetTimer(NULL,1,100,NULL):0;
 puts("{\"kind\":\"FILTER_READY\"}");fflush(stdout);
 while(GetMessageW(&msg,NULL,0,0)>0){
  if(msg.message==WM_TIMER&&!repairing)repair(NULL);
  else{TranslateMessage(&msg);DispatchMessageW(&msg);}
 }
 if(timer)KillTimer(NULL,timer);
 UnhookWindowsHookEx(hook);
 InterlockedExchange(&closing,1);CloseHandle(thread);
 puts("{\"kind\":\"FILTER_STOPPED\"}");fflush(stdout);return 0;
}
