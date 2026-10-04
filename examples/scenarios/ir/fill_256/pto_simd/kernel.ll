; ModuleID = 'ptoas.hivm.official.vector'
source_filename = "ptoas.hivm.official.vector"

declare i64 @llvm.hivm.GET.CTRL()

declare i64 @llvm.hivm.SBITSET0(i64, i64)

declare void @llvm.hivm.SET.CTRL(i64)

declare void @llvm.hivm.SET.LOOP.SIZE.UBTOOUT(i64)

declare void @llvm.hivm.SET.LOOP.SIZE.OUTTOUB(i64)

declare void @llvm.hivm.SET.ST.ATOMIC.CFG(i64)

declare <256 x i1> @llvm.hivm.pset.b32(i32)

declare <64 x float> @llvm.hivm.vdups.z.v64f32(float, <256 x i1>, i32)

declare void @llvm.hivm.vstsx1.v64f32(<64 x float>, ptr addrspace(6), i32, i32, i32, <256 x i1>)

declare void @llvm.hivm.SET.FLAG.IMM(i64, i64, i64)

declare void @llvm.hivm.WAIT.FLAG.IMM(i64, i64, i64)

declare void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1), ptr addrspace(6), i64, i64)

define void @main_kernel_mix_aiv(ptr addrspace(1) %0) #0 {
  %2 = call i64 @llvm.hivm.GET.CTRL()
  %3 = call i64 @llvm.hivm.SBITSET0(i64 %2, i64 60)
  call void @llvm.hivm.SET.CTRL(i64 %3)
  %4 = call i64 @llvm.hivm.GET.CTRL()
  %5 = and i64 %4, 281474976710656
  %6 = or i64 %5, 1152921504606846984
  call void @llvm.hivm.SET.CTRL(i64 %6)
  call void @llvm.hivm.SET.LOOP.SIZE.UBTOOUT(i64 2097153)
  call void @llvm.hivm.SET.LOOP.SIZE.OUTTOUB(i64 2097153)
  call void @llvm.hivm.SET.ST.ATOMIC.CFG(i64 36)
  br label %7

7:                                                ; preds = %aivscope.latch, %1
  %8 = phi i64 [ %24, %aivscope.latch ], [ 0, %1 ]
  %9 = icmp slt i64 %8, 1
  br i1 %9, label %10, label %25

10:                                               ; preds = %7
  %11 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  %12 = call <64 x float> @llvm.hivm.vdups.z.v64f32(float 1.250000e+00, <256 x i1> %11, i32 1)
  br label %13

13:                                               ; preds = %16, %10
  %14 = phi i16 [ %22, %16 ], [ 0, %10 ]
  %15 = icmp slt i16 %14, 4
  br i1 %15, label %16, label %23

16:                                               ; preds = %13
  %17 = sext i16 %14 to i64
  %18 = trunc i64 %17 to i32
  %19 = mul i32 %18, 64
  %20 = sext i32 %19 to i64
  %21 = getelementptr float, ptr addrspace(6) null, i64 %20
  call void @llvm.hivm.vstsx1.v64f32(<64 x float> %12, ptr addrspace(6) %21, i32 0, i32 2, i32 0, <256 x i1> %11)
  %22 = add i16 %14, 1
  br label %13

23:                                               ; preds = %13
  br label %aivscope.latch

aivscope.latch:                                   ; preds = %23
  %24 = add i64 %8, 1
  br label %7, !llvm.loop !3

25:                                               ; preds = %7
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %0, ptr addrspace(6) null, i64 4611686052787126288, i64 1125899906843648)
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

