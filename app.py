# ---------------------------
# SAVE CLIENT (FIXED)
# ---------------------------
if st.button("Save Client"):
    if name.strip() == "":
        st.error("Enter client name")

    elif name in clients_df["Name"].values:
        # 🔴 UPDATE EXISTING (NO DUPLICATE)
        clients_df.loc[clients_df["Name"] == name, ["Equity", "Value"]] = [equity, value]
        save_clients(clients_df)

        st.success("Client updated successfully!")

    else:
        # 🟢 NEW CLIENT
        new = pd.DataFrame([[name, equity, value]],
                           columns=["Name", "Equity", "Value"])
        clients_df = pd.concat([clients_df, new], ignore_index=True)
        save_clients(clients_df)

        st.success("Client added successfully!")

    st.session_state["selected_client"] = name
    st.rerun()
