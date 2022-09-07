//
//  ModEx.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/6/22.
//

import Foundation

import SwiftUI

fileprivate struct FloatingPanelModifier<PanelContent: View>: ViewModifier {
    @Binding var isPresented: Bool
 
    var contentRect: CGRect = CGRect(x: 0, y: 0, width: 624, height: 512)
 
    @ViewBuilder let view: () -> PanelContent
 
    @State var panel: FloatingPanel<PanelContent>?
 
    func body(content: Content) -> some View {
        content
            .onAppear {
                panel = FloatingPanel(view: view, contentRect: contentRect, isPresented: $isPresented)
                panel?.center()
                if isPresented {
                    present()
                }
            }.onDisappear {
                panel?.close()
                panel = nil
            }.onChange(of: isPresented) { value in
                if value {
                    present()
                } else {
                    panel?.close()
                }
            }
    }
    
    func present() {
        panel?.orderFront(nil)
        panel?.makeKey()
    }
}

extension View {
    func floatingPanel<Content: View>(isPresented: Binding<Bool>,
                                      contentRect: CGRect = CGRect(x: 0, y: 0, width: 624, height: 512),
                                      @ViewBuilder content: @escaping () -> Content) -> some View {
        self.modifier(FloatingPanelModifier(isPresented: isPresented, contentRect: contentRect, view: content))
    }
}
