#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <imm.h>
#include <stdio.h>
int main(void) {
    HWND fg=GetForegroundWindow(); DWORD pid=0,tid=GetWindowThreadProcessId(fg,&pid);
    GUITHREADINFO g={0}; g.cbSize=sizeof(g); BOOL ok=GetGUIThreadInfo(tid,&g);
    POINT cursor={0}; BOOL cp=GetCursorPos(&cursor);
    DWORD_PTR pong=0; BOOL responsive=fg?SendMessageTimeoutW(fg,WM_NULL,0,0,SMTO_ABORTIFHUNG,250,&pong)!=0:FALSE;
    printf("{\"pid\":%lu,\"thread\":%lu,\"gui_valid\":%s,\"flags\":%lu,",pid,tid,ok?"true":"false",g.flags);
    printf("\"foreground\":\"%p\",\"active\":\"%p\",\"focus\":\"%p\",\"capture\":\"%p\",",fg,g.hwndActive,g.hwndFocus,g.hwndCapture);
    printf("\"menuOwner\":\"%p\",\"caretOwner\":\"%p\",\"caretRect\":[%ld,%ld,%ld,%ld],",g.hwndMenuOwner,g.hwndCaret,g.rcCaret.left,g.rcCaret.top,g.rcCaret.right,g.rcCaret.bottom);
    printf("\"layout\":\"%p\",\"responsive\":%s,\"cursorValid\":%s,\"cursor\":[%ld,%ld],",GetKeyboardLayout(tid),responsive?"true":"false",cp?"true":"false",cursor.x,cursor.y);
    const int keys[]={VK_SHIFT,VK_CONTROL,VK_MENU,VK_LWIN,VK_RWIN,VK_CAPITAL,VK_BACK};
    const char *names[]={"shift","control","alt","superL","superR","caps","back"};
    printf("\"asyncHighBits\":{");
    for(unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)printf("%s\"%s\":%d",i?",":"",names[i],!!(GetAsyncKeyState(keys[i])&0x8000));
    printf("},\"observerQueueHighBits\":{");
    for(unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)printf("%s\"%s\":%d",i?",":"",names[i],!!(GetKeyState(keys[i])&0x8000));
    HIMC im=g.hwndFocus?ImmGetContext(g.hwndFocus):0;
    printf("},\"imeContextAvailable\":%s,\"imeOpen\":%s}\n",im?"true":"false",im&&ImmGetOpenStatus(im)?"true":"false");
    if(im)ImmReleaseContext(g.hwndFocus,im);
    return ok?0:1;
}
