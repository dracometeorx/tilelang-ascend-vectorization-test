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
  %9 = phi i64 [ %40, %aivscope.latch ], [ 0, %2 ]
  %10 = icmp slt i64 %9, 1
  br i1 %10, label %11, label %41

11:                                               ; preds = %8
  br label %12

12:                                               ; preds = %37, %11
  %13 = phi i16 [ %38, %37 ], [ 0, %11 ]
  %14 = icmp slt i16 %13, 64
  br i1 %14, label %15, label %39

15:                                               ; preds = %12
  %16 = sext i16 %13 to i64
  %17 = trunc i64 %16 to i32
  %18 = add i32 %17, 256
  %19 = zext i32 %18 to i64
  %20 = getelementptr float, ptr addrspace(6) null, i64 %19
  store float 0.000000e+00, ptr addrspace(6) %20, align 4
  br label %21

21:                                               ; preds = %24, %15
  %22 = phi i16 [ %36, %24 ], [ 0, %15 ]
  %23 = icmp slt i16 %22, 4
  br i1 %23, label %24, label %37

24:                                               ; preds = %21
  %25 = sext i16 %22 to i64
  %26 = trunc i64 %25 to i32
  %27 = getelementptr float, ptr addrspace(6) null, i64 %19
  %28 = load float, ptr addrspace(6) %27, align 4
  %29 = mul i32 %26, 64
  %30 = add i32 %29, %17
  %31 = zext i32 %30 to i64
  %32 = getelementptr float, ptr addrspace(6) null, i64 %31
  %33 = load float, ptr addrspace(6) %32, align 4
  %34 = fadd float %28, %33
  %35 = getelementptr float, ptr addrspace(6) null, i64 %19
  store float %34, ptr addrspace(6) %35, align 4
  %36 = add i16 %22, 1
  br label %21

37:                                               ; preds = %21
  %38 = add i16 %13, 1
  br label %12

39:                                               ; preds = %12
  br label %aivscope.latch

aivscope.latch:                                   ; preds = %39
  %40 = add i64 %9, 1
  br label %8, !llvm.loop !3

41:                                               ; preds = %8
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %1, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), i64 4611686027017322512, i64 281474976710912)
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

