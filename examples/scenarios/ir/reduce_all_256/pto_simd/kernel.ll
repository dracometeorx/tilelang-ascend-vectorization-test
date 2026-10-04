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

declare void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1), ptr addrspace(6), i64, i64)

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
  br label %8

8:                                                ; preds = %aivscope.latch, %2
  %9 = phi i64 [ %23, %aivscope.latch ], [ 0, %2 ]
  %10 = icmp slt i64 %9, 1
  br i1 %10, label %11, label %24

11:                                               ; preds = %8
  store float 0.000000e+00, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), align 4
  br label %12

12:                                               ; preds = %15, %11
  %13 = phi i16 [ %21, %15 ], [ 0, %11 ]
  %14 = icmp slt i16 %13, 256
  br i1 %14, label %15, label %22

15:                                               ; preds = %12
  %16 = sext i16 %13 to i64
  %17 = load float, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), align 4
  %18 = getelementptr float, ptr addrspace(6) null, i64 %16
  %19 = load float, ptr addrspace(6) %18, align 4
  %20 = fadd float %17, %19
  store float %20, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), align 4
  %21 = add i16 %13, 1
  br label %12

22:                                               ; preds = %12
  br label %aivscope.latch

aivscope.latch:                                   ; preds = %22
  %23 = add i64 %9, 1
  br label %8, !llvm.loop !3

24:                                               ; preds = %8
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %1, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), i64 4611686018561605648, i64 4398046511108)
  ret void
}

attributes #0 = { "target-cpu"="dav-c310-vec" "target-features"="+ATOMIC,+ArchV130,+AregRedefinable,+ArithmeticBf16,+AtomicForB8 ,+F8e4m3,+F8e5m2,+F8e8m0,+FFTSBlk,+Fp4e1m2x2,+Fp4e2m1x2,+LDExtRefine,+MOVX8,+SPR7bits,+SyncV,+dav-c310-vec" }

!llvm.module.flags = !{!0}
!hivm.annotations = !{!1, !2}

!0 = !{i32 2, !"Debug Info Version", i32 3}
!1 = !{ptr @main_kernel_mix_aiv, !"kernel", i32 1}
!2 = !{ptr @main_kernel_mix_aiv, !"kernel_with_simd", i32 1}
!3 = distinct !{!3, !4}
!4 = !{!"llvm.loop.aivector_scope"}

