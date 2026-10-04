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
  call void @llvm.hivm.store.vfsimt.info(i64 4295032960)
  call simt_entry void @main_kernel_simt_0(ptr addrspace(6) null)
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %2, ptr addrspace(6) getelementptr (float, ptr addrspace(6) null, i64 256), i64 4611686052787126288, i64 1125899906843648)
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
  %11 = ashr i32 %2, 5
  %12 = add i32 %11, 512
  %13 = sext i32 %12 to i64
  %14 = getelementptr float, ptr addrspace(6) %0, i64 %13
  %15 = load float, ptr addrspace(6) %14, align 4
  %16 = insertelement <2 x float> undef, float %15, i32 0
  %17 = insertelement <2 x float> %16, float %15, i32 1
  %18 = fadd <2 x float> %10, %17
  %19 = add i32 %3, 256
  %20 = sext i32 %19 to i64
  %21 = mul i64 %20, 4
  %22 = add i64 %5, %21
  %23 = inttoptr i64 %22 to ptr addrspace(6)
  %24 = getelementptr <2 x float>, ptr addrspace(6) %23, i64 0
  store <2 x float> %18, ptr addrspace(6) %24, align 8
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

