; ModuleID = 'ptoas.hivm.official.vector'
source_filename = "ptoas.hivm.official.vector"

declare i64 @llvm.hivm.GET.CTRL()

declare i64 @llvm.hivm.SBITSET0(i64, i64)

declare void @llvm.hivm.SET.CTRL(i64)

declare void @llvm.hivm.SET.LOOP.SIZE.UBTOOUT(i64)

declare void @llvm.hivm.SET.LOOP.SIZE.OUTTOUB(i64)

declare void @llvm.hivm.SET.ST.ATOMIC.CFG(i64)

declare void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.u8.DV(ptr addrspace(6), ptr addrspace(1), i64, i64)

declare void @llvm.hivm.SET.FLAG.IMM(i64, i64, i64)

declare void @llvm.hivm.WAIT.FLAG.IMM(i64, i64, i64)

declare void @llvm.hivm.store.vfsimt.info(i64)

declare void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1), ptr addrspace(6), i64, i64)

declare i32 @llvm.hivm.get.TID.X()

define void @main_kernel_mix_aiv(ptr addrspace(1) %0, ptr addrspace(1) %1) #0 {
  %3 = call i64 @llvm.hivm.GET.CTRL()
  %4 = call i64 @llvm.hivm.SBITSET0(i64 %3, i64 60)
  call void @llvm.hivm.SET.CTRL(i64 %4)
  %5 = call i64 @llvm.hivm.GET.CTRL()
  %6 = and i64 %5, 281474976710656
  %7 = or i64 %6, 1152921504606846984
  call void @llvm.hivm.SET.CTRL(i64 %7)
  call void @llvm.hivm.SET.LOOP.SIZE.UBTOOUT(i64 2097153)
  call void @llvm.hivm.SET.LOOP.SIZE.OUTTOUB(i64 2097153)
  call void @llvm.hivm.SET.ST.ATOMIC.CFG(i64 36)
  call void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.u8.DV(ptr addrspace(6) null, ptr addrspace(1) %0, i64 34359738384, i64 1125899906843648)
  call void @llvm.hivm.SET.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.store.vfsimt.info(i64 4295032960)
  call simt_entry void @main_kernel_simt_0(ptr addrspace(6) null)
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %1, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), i64 4611686052787126288, i64 1125899906843648)
  ret void
}

; Function Attrs: noinline
define linkonce_odr simt_entry void @main_kernel_simt_0(ptr addrspace(6) %0) #1 !annotation !6 !annotation !7 {
  %2 = call i32 @llvm.hivm.get.TID.X()
  %3 = mul i32 %2, 2
  %4 = sext i32 %3 to i64
  %5 = ptrtoint ptr addrspace(6) %0 to i64
  %6 = mul i64 %4, 4
  %7 = add i64 %5, %6
  %8 = inttoptr i64 %7 to ptr addrspace(6)
  %9 = getelementptr <2 x float>, ptr addrspace(6) %8, i64 0
  %10 = load <2 x float>, ptr addrspace(6) %9, align 8
  %11 = fadd <2 x float> %10, <float 1.250000e+00, float 1.250000e+00>
  %12 = add i32 %3, 256
  %13 = sext i32 %12 to i64
  %14 = mul i64 %13, 4
  %15 = add i64 %5, %14
  %16 = inttoptr i64 %15 to ptr addrspace(6)
  %17 = getelementptr <2 x float>, ptr addrspace(6) %16, i64 0
  store <2 x float> %11, ptr addrspace(6) %17, align 8
  ret void
}

attributes #0 = { "target-cpu"="dav-c310-vec" "target-features"="+ATOMIC,+ArchV130,+AregRedefinable,+ArithmeticBf16,+AtomicForB8 ,+F8e4m3,+F8e5m2,+F8e8m0,+FFTSBlk,+Fp4e1m2x2,+Fp4e2m1x2,+LDExtRefine,+MOVX8,+SPR7bits,+SyncV,+dav-c310-vec" }
attributes #1 = { noinline "target-cpu"="dav-c310-vec" "target-features"="+ATOMIC,+ArchV130,+AregRedefinable,+ArithmeticBf16,+AtomicForB8 ,+F8e4m3,+F8e5m2,+F8e8m0,+FFTSBlk,+Fp4e1m2x2,+Fp4e2m1x2,+LDExtRefine,+MOVX8,+SPR7bits,+SyncV,+dav-c310-vec" }

!llvm.module.flags = !{!0}
!hivm.annotations = !{!1, !2, !3, !4, !5}

!0 = !{i32 2, !"Debug Info Version", i32 3}
!1 = !{ptr @main_kernel_mix_aiv, !"kernel", i32 1}
!2 = !{ptr @main_kernel_mix_aiv, !"kernel_with_simd", i32 1}
!3 = !{ptr @main_kernel_mix_aiv, !"kernel_with_simt", i32 1}
!4 = distinct !{null, !"simt-max-threads", i32 128}
!5 = distinct !{null, !"simt-max-registers", i32 128}
!6 = !{!"simt-max-threads", i32 128}
!7 = !{!"simt-max-registers", i32 128}

