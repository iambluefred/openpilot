// BUS 0 is on the LKAS module (ASCM) side
// BUS 2 is on the actuator (EPS) side

static int gm_ascm_fwd_hook(int bus_num, CAN_FIFOMailBox_TypeDef *to_fwd) {

  uint32_t addr = to_fwd->RIR>>21;
// CAN 1
  if (bus_num == 1) {
    // Mask CAN ID
    if((addr == 0x24 )||(addr == 0x25 )||(addr == 0xAA )||(addr == 0xB4 )||
//       (addr == 0x224 )||(addr == 0x230)||(addr == 0x260)||(addr == 0x283)||
       (addr == 0x262 )||(addr == 0x230)||(addr == 0x260)||(addr == 0x283)||
       (addr == 0x399)||(addr == 0x3B7)||(addr == 0x3BC)||(addr == 0x489)||
       (addr == 0x48A)||(addr == 0x48B)||(addr == 0x611)||(addr == 0x614)||
       (addr == 0x620)||(addr == 0x622)||(addr == 0x1C4)) {
      return 0;
    }
    // 0x361 to fake 0x1D2
    if (addr == 0x361){
      int button = ((to_fwd->RDLR) & 0x0004) >> 2;
      switch (button) {
        case 1:  // cancel
          (to_fwd->RIR ) = 0x1D2<<21 ;
          (to_fwd->RDHR) = 0x7B800000 ; 
          (to_fwd->RDLR) = 0x00000020 ;
          break;
        default:
          (to_fwd->RIR ) = 0x1D2<<21 ;
          (to_fwd->RDHR) = 0xDB000000 ; 
          (to_fwd->RDLR) = 0x00000000 ;
          break; // any other button is irrelevant
      }
     return 0; 
    }
    // 0x3A0 to fake 0x1D3
    if (addr == 0x3A0){
      (to_fwd->RIR ) = 0x1D3<<21 ;
      (to_fwd->RDHR) = 0xC0000000 ; // low 
      (to_fwd->RDLR) = 0x003CA800 ; // high
     return 0;
    }
    // 0x224 Brake module
    if (addr == 0x224){
      (to_fwd->RIR ) = 0x224<<21 ;
      (to_fwd->RDHR) = 0x080000000 ; // low 
      (to_fwd->RDLR) = 0x000000000 ; // high
     return 0;
    }
    // fake camera 0x2E4
    if ((addr == 0x1AA) || (addr == 0x127)){
    (to_fwd->RIR ) = 0x2E4<<21 ;
    (to_fwd->RDHR) = 0xC0000000 ; // low 
    (to_fwd->RDLR) = 0x003CA800 ; // high
    return 2;
     }
    
    
  } 
// CAN 0
  if (bus_num == 0) {
     return 1;
  }
  return -1;
}

const safety_hooks gm_ascm_hooks = {
  .init = nooutput_init,
  .rx = default_rx_hook,
  .tx = alloutput_tx_hook,
  .tx_lin = nooutput_tx_lin_hook,
  .ignition = default_ign_hook,
  .fwd = gm_ascm_fwd_hook,
  .relay = nooutput_relay_hook,
};



// static int gm_ascm_fwd_hook(int bus_num, CAN_FIFOMailBox_TypeDef *to_fwd) {
// 
//   uint32_t addr = to_fwd->RIR>>21;
//   if ((bus_num == 1)&& ((addr == 0x24 )||(addr == 0x25 )||(addr == 0xa6 )||(addr == 0xaa )||
//                         (addr == 0xb4 )||(addr == 0x161)||(addr == 0x167)||(addr == 0x1d2)||
//                         (addr == 0x1D3)||(addr == 0x224)||(addr == 0x228)||(addr == 0x230)||
//                         (addr == 0x260)||(addr == 0x262)||(addr == 0x266)||(addr == 0x283)||
//                         (addr == 0x2c1)||(addr == 0x2e4)||(addr == 0x2e6)||(addr == 0x343)||
//                         (addr == 0x399)||(addr == 0x3b7)||(addr == 0x3bc)||(addr == 0x411)||
//                         (addr == 0x412)||(addr == 0x489)||(addr == 0x48a)||(addr == 0x48b)||
//                         (addr == 0x611)||(addr == 0x614)||(addr == 0x620)||(addr == 0x622))) {
//       return 0;
//     }
// 
// 
// 
// 
// 
// 
//   if (bus_num == 1) {
//     if (addr == 0x361){
//       int button = ((to_fwd->RDLR) & 0x0004) >> 2;
//       switch (button) {
//         case 1:  // cancel
//           (to_fwd->RIR ) = 0x1D2<<21 ;
//           (to_fwd->RDHR) = 0x7B800000 ; 
//           (to_fwd->RDLR) = 0x00000020 ;
//           break;
//         default:
//           (to_fwd->RIR ) = 0x1D2<<21 ;
//           (to_fwd->RDHR) = 0xDB000000 ; 
//           (to_fwd->RDLR) = 0x00000000 ;
//           break; // any other button is irrelevant
//       }
//      return 0; 
//      }
// 
//     if (addr == 0x3A0){
//     (to_fwd->RIR ) = 0x1D3<<21 ;
//     (to_fwd->RDHR) = 0xC0000000 ; // low 
//     (to_fwd->RDLR) = 0x003CA800 ; // high
//     return 0;
//      }
// 
//     if ((addr == 0x24) || (addr == 0x25)){
//     (to_fwd->RIR ) = 0x687<<21 ;
//     (to_fwd->RDHR) = 0xC0000000 ; // low 
//     (to_fwd->RDLR) = 0x003CA800 ; // high
//     return 2;
//      }
//    return 0;
//   }
//   if (bus_num == 0) {
//      return 1;
//   }
//   return -1;
// }

//    (to_fwd->RIR ) = 0x1D3<<21 ;
//    (to_fwd->RDHR) = 0x7B800000 ; 
//    (to_fwd->RDLR) = 0x00000020 ;
//  if ((bus_num == 0) && (addr == 0x361)) {
//    cruisedata = ((to_fwd->RDLR) & 0x0004) ;
//    if ((cruisedata == 0x04)) {
//      // LKA = enable
//      (to_fwd->RIR ) = 0x1D2<<21 ;
//    (to_fwd->RDHR) = 0x7B800000 ; 
//    (to_fwd->RDLR) = 0x00000020 ;
//      return 0;
//    }
//    else {
//      // LKA = disable
//      (to_fwd->RIR ) = 0x1D2<<21 ;
//      (to_fwd->RDHR) = 0xDB000000 ; 
//      (to_fwd->RDLR) = 0x00000000 ;
//      return 0;
//    }
//  }
//  if ((bus_num == 0) && (addr == 0x3A0)) {
//    (to_fwd->RIR ) = 0x1D3<<21 ;
////    (to_fwd->RDHR) = 0x7B800000 ; 
////    (to_fwd->RDLR) = 0x00000020 ;
//    (to_fwd->RDHR) = 0xC0000000 ; // low 
//    (to_fwd->RDLR) = 0x003CA800 ; // high
//    return 0;
//  }