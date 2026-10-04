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

declare <256 x i1> @llvm.hivm.pset.b32(i32)

declare <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6), i32, i32, i32)

declare <64 x float> @llvm.hivm.vadd.s.x.v64f32(<64 x float>, <64 x float>, <256 x i1>)

declare void @llvm.hivm.vstsx1.v64f32(<64 x float>, ptr addrspace(6), i32, i32, i32, <256 x i1>)

declare void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1), ptr addrspace(6), i64, i64)

define void @main_kernel_mix_aiv(ptr addrspace(1) %0, ptr addrspace(1) %1, ptr addrspace(1) %2) #0 {
  %4 = call i64 @llvm.hivm.GET.CTRL()
  %5 = call i64 @llvm.hivm.SBITSET0(i64 %4, i64 60)
  call void @llvm.hivm.SET.CTRL(i64 %5)
  %6 = call i64 @llvm.hivm.GET.CTRL()
  %7 = and i64 %6, 281474976710656
  %8 = or i64 %7, 1152921504606846984
  call void @llvm.hivm.SET.CTRL(i64 %8)
  call void @llvm.hivm.SET.LOOP.SIZE.UBTOOUT(i64 2097153)
  call void @llvm.hivm.SET.LOOP.SIZE.OUTTOUB(i64 2097153)
  call void @llvm.hivm.SET.ST.ATOMIC.CFG(i64 36)
  call void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.u8.DV(ptr addrspace(6) null, ptr addrspace(1) %0, i64 34359738384, i64 1125899906843648)
  call void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.u8.DV(ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 512), ptr addrspace(1) %1, i64 536870928, i64 17592186044432)
  call void @llvm.hivm.SET.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 4, i64 1, i64 0)
  br label %9

9:                                                ; preds = %aivscope.latch, %3
  %10 = phi i64 [ %34, %aivscope.latch ], [ 0, %3 ]
  %11 = icmp slt i64 %10, 1
  br i1 %11, label %12, label %35

12:                                               ; preds = %9
  %13 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  br label %14

14:                                               ; preds = %17, %12
  %15 = phi i16 [ %32, %17 ], [ 0, %12 ]
  %16 = icmp slt i16 %15, 4
  br i1 %16, label %17, label %33

17:                                               ; preds = %14
  %18 = sext i16 %15 to i64
  %19 = trunc i64 %18 to i32
  %20 = add i32 %19, 512
  %21 = sext i32 %20 to i64
  %22 = getelementptr float, ptr addrspace(6) null, i64 %21
  %23 = mul i32 %19, 64
  %24 = sext i32 %23 to i64
  %25 = getelementptr float, ptr addrspace(6) null, i64 %24
  %26 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %22, i32 0, i32 3, i32 0)
  %27 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %25, i32 0, i32 0, i32 0)
  %28 = add i32 %23, 256
  %29 = sext i32 %28 to i64
  %30 = getelementptr float, ptr addrspace(6) null, i64 %29
  %31 = call <64 x float> @llvm.hivm.vadd.s.x.v64f32(<64 x float> %27, <64 x float> %26, <256 x i1> %13)
  call void @llvm.hivm.vstsx1.v64f32(<64 x float> %31, ptr addrspace(6) %30, i32 0, i32 2, i32 0, <256 x i1> %13)
  %32 = add i16 %15, 1
  br label %14

33:                                               ; preds = %14
  br label %aivscope.latch

aivscope.latch:                                   ; preds = %33
  %34 = add i64 %10, 1
  br label %9, !llvm.loop !3

35:                                               ; preds = %9
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %2, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), i64 4611686052787126288, i64 1125899906843648)
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

